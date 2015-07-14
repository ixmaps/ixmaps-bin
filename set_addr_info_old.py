#!/usr/bin/python

"""
The primary purpose of set_addr_info.py  is to populate the fields
of the ip_addr_info table, when invoked with the -u flag.  For
each row of the ip_addr_info table that has the default value of 'N' in the
p_status field, all of the fields other than the ip_addr field are updated.
The fields are:

ip_addr       is the IPv4 address and is the primary key of the table.
asnum         is the originating autonomous system number as seen by iPlane
hostname      is the fully-qualified host name of the IP address.
lat           is the best latitude estimate
long          is the best longitude estimate
mm_lat        is the latitude estimate from the MaxMind GeoCityLite database.
mm_long       is the longitude estimate from the MaxMind GeoCityLite database.
mm_country    is from the MaxMind GeoCityLite database.
mm_region     is a 2-character region (province/state/whatever) from the MaxMind
              GeoCityLite database.  It is not expanded for non US and Canada.
mm_city       is from the MaxMind GeoCityLite database.
mm_pcode      is a postal/zip code (N.A. only) from the MaxMind GeoCityLite database.
mm_area_code  is a telephone area code (US only) from the MaxMind GeoCityLite database.
mm_dma_code   is a telephone dma code (US only) from the MaxMind GeoCityLite database.
p_status      defaults to 'N' for newly created entries. set to blank when completed.


This program (using -u) is suited to be run periodically from a cron job.
"""

import socket
from socket import socket, AF_UNIX, SOCK_DGRAM, getfqdn
import os
import sys
import re
import math
import pg
import time
import string
from ixmaps import DBConnect, EARTH_MEAN_RADIUS, ll_to_xyz, distance_km, dq_to_num, num_to_dq, ASNumSockLookup, get_range_id
from ixmaps import MutexFile

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def get_unknown_ip_addrs(conn):
    qres = conn.query("select ip_addr from ip_addr_info where p_status='N'")
    return [d['ip_addr'] for d in qres.dictresult()]

def update_ip_addr_info(conn, ip_addr, asnum, mm, hostname):
    #print asnum
    try:
        asn = int(asnum)
    except ValueError:
        # instead of a single AS# we have an AS-set or AS-path
        # (or both).  The origin AS is considered to be the last AS#, per
        # http://iplane.cs.washington.edu/data.html
        sa = [c for c in asnum]
        while not ('0' <= sa[-1] <= '9'):
            del sa[-1]
        i = -1
        while '0' <= sa[i] <= '9':
            i -= 1
        asn = int(''.join(sa[i+1:]))
    if mm:
        (lat, long) = (mm.lat, mm.long)
    else:
        (lat, long) = (0.0, 0.0)
    #sometimes these can still be None
    if not lat:
        lat = 0.0
    if not long:
        long = 0.0

    # marshal formats and data.  If MaxMind data is absent (lookup failed)
    # then only the lat/long will be set (to 0.0,0.0)
    set_str = "set asnum=%d, lat=%f, long=%f, mm_lat=%f, mm_long=%f, hostname='%s', p_status='%s'"
    data = [asn, lat, long, lat, long, hostname, ' ']
    if mm:
        def us2bl(s):
            s = "''".join(s.split("'"))   # render "St. John's" properly
            s = string.replace(s, "_", " ")
            return unicode(s, 'latin1', 'ignore').encode('utf-8')
        set_str += ", mm_country='%s', mm_region='%s', mm_city='%s', mm_postal='%s', mm_area_code=%d, mm_dma_code=%d "
        data += [mm.country, us2bl(mm.region), us2bl(mm.city), us2bl(mm.pcode), mm.area_c, mm.dma_c]       
    print data, ip_addr
    qstr = ("update ip_addr_info "+set_str+"where ip_addr='%s'") % tuple(data+[ip_addr])
    print qstr
    conn.query(qstr)
    # if the Autonomous System number is invalid, request a whois lookup on the network
    if asn < 1:
        # only make the request if the network is hitherto unknown
        if not get_range_id(conn, ip_addr):
            os.system("arin_whois.py -n %s" % ip_addr)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class MaxMindLookup(object):
    def __init__(self, query_mode="A"):
        pid = os.getpid()
        self.sock_filename = "/tmp/geoloc-%d.sock" % pid
        self.query_mode = query_mode;
        try:
            os.remove(self.sock_filename)
        except OSError:
            pass
        self.gs = socket(AF_UNIX, SOCK_DGRAM, 0)
        self.gs.bind(self.sock_filename)

    def query_dquad(self, dquad):
        self.gs.sendto(self.query_mode+dquad, MaxMindLookup.MM_SOCKET)
        buf = self.gs.recv(128)
        return buf

    def __del__(self):
        self.gs.close()
        os.remove(self.sock_filename)
    
    MM_SOCKET = "/tmp/MaxMind-GLC.sock"

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ASNumPretendLookup(object):
    def __init__(self):
        pass

    def query_dquad(self, dquad):
        # for now, generate fake AS# from first 16-bits
        dqa = [int(s) for s in dquad.split(".")]
        return (str(256*dqa[0] + dqa[1]), 0, 0, 0)

class ASNumRealLookup(object):
    def __init__(self, bgp_table):
        po=re.compile("^([0-9.]+)/([0-9]+) ([0-9_]+)$")
        masks=[(0xffffffff&((-1)<<i)) for i in range(32,-1,-1)]
        bt=[None]*33
        for i in range(33):
            bt[i] = {}
        fd = open(bgp_table)
        while True:
            line = fd.readline()
            if len(line) == 0:
                break
            mo = po.match(line)
            if mo:
                 (pfx, plen, asn) = mo.groups()
                 plen = int(plen)
                 pfxbin = dq_to_num(pfx) & masks[plen]
                 bt[plen][pfxbin] = asn
        fd.close()
        self.masks = masks
        self.bt = bt

    def query_dquad(self, dquad):
        num = dq_to_num(dquad)
        plen = 0
        masks = self.masks
        bt = self.bt
        for i in range(32,-1,-1):
            masked_num = num & masks[i]
            if bt[i].has_key(masked_num):
                return (bt[i][masked_num], i, masked_num, num)
        return (0,0,0,0)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class MaxMindPoint(object):
    def __init__(self, qs):
        (self.prefix, arrow, self.country, self.region, self.city, \
         self.pcode, self.lat, self.long, self.area_c, self.dma_c) = qs.split(" ")
        self.lat = float(self.lat)
        self.long = float(self.long)
        self.area_c = int(self.area_c)
        self.dma_c = int(self.dma_c)

    def __repr__(self):
        return "(%s:%s:%s:%s:%s:%s:%s:%s:%s)" % (self.prefix, self.country, self.region, self.city, \
            self.pcode, str(self.lat), str(self.long), str(self.area_c), str(self.dma_c))

class TRNode(object):
    def __init__(self, ipaddr, latency):
        self.ipaddr = ipaddr
        self.fqdn = None
        self.dquad = num_to_dq(ipaddr)
        self.latency = latency
        self.asnum = None
        self.mm = None     # from the MaxMind database
        self.xyz = (0.0, 0.0, 0.0)
        self.ch_num = None
        self.interest = None

    def __repr__(self):
        return "(%s:%g:%s:%s:%s:%s:%s)" % (self.dquad, self.latency, self.asnum, str(self.mm), str(self.ch_num), str(self.interest), str(self.fqdn))

    def lookup_geoloc(self, ml):
        qs = ml.query_dquad(self.dquad)
        print qs
        try:
            qs.index("-> NULL")
        except ValueError:
            self.mm = MaxMindPoint(qs)
            self.set_geoloc(float(self.mm.lat), float(self.mm.long))

    def lookup_chotel(self, cl, min_distance_km=13.000):
        (hotel, distance) = CHotel.closest(cl, self.xyz)
        if distance < min_distance_km:
            self.ch_num = hotel

    def set_geoloc(self, lat, long):
        self.lat = lat
        self.long = long
        self.xyz = ll_to_xyz(lat,long)

    def set_fqdn(self):
        self.fqdn = getfqdn(self.dquad)

    def lookup_asnum(self, al):
        self.asnum = al.query_dquad(self.dquad)[0]

    def set_asn(self, asnum):
        self.asnum = asnum

    def distance(self, point):
        return distance_km(self.xyz, point)

    def update_db(self, conn):
        update_ip_addr_info(conn, self.dquad, self.asnum, self.mm, self.fqdn)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class InterestAttribute(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "%d:%s" % (self.id, self.name)

    @staticmethod
    def factory(s):
        sa = s.split(":")
        return InterestAttribute(int(sa[0]), sa[1])

class CHOwner(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "%d:%s" % (self.id, self.name)

    @staticmethod
    def factory(s):
        sa = s.split(":")
        return CHOwner(int(sa[0]), sa[1])

class CHotel(object):
    def __init__(self, id, name, lat, long, owner):
        self.id = id
        self.name = name
        self.lat = lat
        self.long = long
        if id:
            self.xyz = ll_to_xyz(lat,long)
        else:
            self.xyz = (0.0, 0.0, 0.0)
        self.owner = owner

    def __repr__(self):
        return "%d:%s:%g:%g:%d" % (self.id, self.name, self.lat, self.long, self.owner)

    @staticmethod
    def factory(s):
        sa = s.split(":")
        return CHotel(int(sa[0]), sa[1], float(sa[2]), float(sa[3]), int(sa[4]))

    @staticmethod
    def closest(d, point):
        min_distance = EARTH_MEAN_RADIUS
        index = None
        for id in d:
            curr_distance = distance_km(d[id].xyz, point)
            if curr_distance < min_distance:
                min_distance = curr_distance
                index = id
        return (index, min_distance)
            

def create_from_file(d, factory, fname):
    """Read strings from a file and add items to a dictionary."""
    fd = open(fname)
    for line in fd:
        if line[0] != '#':
            item = factory(line[:-1])
            d[item.id] = item
    fd.close()        
    return d

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


if __name__ == '__main__':
    import getopt
 
    LOCK_FILE="set-addr-info.lock"

    def help():
        print """
Use: set_addr_info.py [options]

Display information ...

Options:
    -u   update the ip_addr_info table in the database 
    -T   pretend to submit a traceroute. Following arguments are one or more
         pairs of IP addresses and round trip times in ms. 
    -I   show interests
    -O   show owners
    -C   show carrier hotels
    -h   this help

Examples:
set_addr_info.py -u
set_addr_info.py -T 12.4.3.4,32 66.44.33.66,112 205.12.17.245,150
    """


    progname = sys.argv[0]
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "hTIOCZu")
    except getopt.GetoptError, exc:
        print >>sys.stderr, "%s: %s" % (progname, str(exc))
        sys.exit(1)

    do_virtual_traceroute = False
    do_debug = False
    do_update_ip_addr_info = False
    show_interests = False
    show_owners = False
    show_chotels = False

    for flag, value in opts:
        if flag == '-T':
            do_virtual_traceroute = True
        elif flag == '-h':
            help()
            sys.exit(0)
        elif flag == '-I':
            show_interests = True
        elif flag == '-O':
            show_owners = True
        elif flag == '-C':
            show_chotels = True
        elif flag == '-Z':
            do_debug = True
        elif flag == '-u':
            do_update_ip_addr_info = True

    ml = MaxMindLookup('A')
    #al = ASNumRealLookup("tiny_bgp.txt")
    #al = ASNumRealLookup("origin_as_mapping.txt")
    al = ASNumSockLookup("A")

    if do_virtual_traceroute:
        tr_elems = [s.split(",") for s in args]
        if do_debug:
            print tr_elems
        tr = [TRNode(dq_to_num(t[0]), float(t[1])) for t in tr_elems]
        if do_debug:
            print tr
        if show_interests:
            interests = create_from_file({}, InterestAttribute.factory, "interests.txt")
            print interests
        if show_owners:
            owners = create_from_file({}, CHOwner.factory, "owners.txt")
            print owners
        if show_chotels:
            chotels = create_from_file({}, CHotel.factory, "chotels.txt")
            print chotels

        for tr_elem in tr:
            tr_elem.lookup_geoloc(ml)
            #print al.query_dquad(tr_elem.dquad)
            tr_elem.lookup_asnum(al)
            if show_chotels:
                tr_elem.lookup_chotel(chotels)
        print tr
        
    elif do_update_ip_addr_info:
        lock=MutexFile(LOCK_FILE)
        if lock.acquire():
            conn = DBConnect.getConnection()
            addrs = get_unknown_ip_addrs(conn)
            #print addrs
            tr = [TRNode(dq_to_num(t), 0.0) for t in addrs]
            for tr_elem in tr:
                tr_elem.lookup_geoloc(ml)
                tr_elem.lookup_asnum(al)
                tr_elem.set_fqdn()
                tr_elem.update_db(conn)
            #print tr
            lock.release()
        else:
            print "cannot acquire lock file"
            sys.exit(0)
    else:
        # just left-over debugging code
        mode = "L"
        start = 1
        if sys.argv[1][0] == '-':
            mode = sys.argv[1][1]
            start = 2
        interests = create_from_file({}, InterestAttribute.factory, "interests.txt")
        print interests
        owners = create_from_file({}, CHOwner.factory, "owners.txt")
        print owners
        chotels = create_from_file({}, CHotel.factory, "chotels.txt")
        print chotels
        for addr in sys.argv[start:]:
            print "%-16s" % addr,
            print ml.query_dquad(addr),
            print " AS"+str(al.query_dquad(addr)[0])
    
    del al
    del ml
