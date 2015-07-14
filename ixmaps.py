#!/usr/bin/python

# IXmaps python utility library

import pg
import os
import math
import string
import re
from socket import socket, AF_UNIX, SOCK_DGRAM, getfqdn

import ixmaps

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# --- Note: Make sure that URL_HOME ends with a slash (/) ---
URL_HOME = "http://dev.ixmaps.ischool.utoronto.ca/"
# URL_HOME = "http://www.ixmaps.ca/"
# URL_HOME = "http://test.n-space.org/ixmaps/"

EARTH_EQUAT_RADIUS = 6378.145    # Equatorial radius in km
EARTH_FLAT = 1.0/298.0           # ellipsoidal flattening at the poles
EARTH_MEAN_RADIUS = EARTH_EQUAT_RADIUS * (1.0 - 0.5*EARTH_FLAT)

MAX_CHOTEL_DIST = 1  # (km)    ## (previously was .5 * MILE_TO_KM)
MAX_NSA_DIST =    20  # (km)    ## (previously was 10 * MILE_TO_KM)

RE_NOTEMPTYLINE = re.compile(r"^(?!$)", re.MULTILINE)
RE_XMLTAG = re.compile(r"^([a-z0-9_]+).*", re.IGNORECASE + re.DOTALL)

# --- Note: I've taken out the MILE_TO_KM.  Just enter these distances
#     in kilometers (kilometers are just as good, yes?) ---
# MILE_TO_KM = 1.609344
MAX_CHOTEL_DIST = .1  # (km)    ## .5 * MILE_TO_KM
MAX_NSA_DIST =    10  # (km)    ## 10 * MILE_TO_KM

# typical use: 
# conn = DBConnect.getConnection()
class DBConnect(object):
    conn = None
    def getConnection():
        if not DBConnect.conn:
            DBConnect.conn = pg.connect("ixmaps", "localhost", 5432)
        return DBConnect.conn
    getConnection = staticmethod(getConnection)


class CHotels(object):
    """    A class for returning lists or dicts containing different subsets
    of the ixmaps-database carrier-hotels."""

    def __init__(self, conn=None, chotels=None):
        if (conn):
            qres = conn.query("select * from chotel")
            try:
                id = qres.dictresult()[0]['id']
            except IndexError:
                raise TracerouteException, "failed to find any carrier hotels"
            self.chotels = qres.dictresult ( )

        elif type(chotels) == list:
            self.chotels = chotels

        elif type(chotels) == dict:
            chotel_list = []
            for chotel in chotels:
                chotel_list.append (chotels[chotel] )
            self.chotels = chotel_list

        else:
            raise TracerouteException, "No database specified, and no traceroute-list given."
            
        location_styles = facility_icons ( )
        for ch in self.chotels:
            ch['xyz'] = ll_to_xyz(ch['lat'], ch['long'])
            # ch['to_render'] = False
            ixclass = get_ch_class(ch)
            ch['ixclass'] = string.replace(ixclass, "near", "", 1)
            ch['facility'] = location_styles[ch['ixclass']]['facility']
            ch['image_esc'] = URL_encode_ampersands(ch['image']) if (ch['image']) else ''
        self.reset()

    def reset(self):
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        try:
            chotels = self.chotels
            index = self.index
            # while not chotels[index]['to_render']:
                # index += 1
            item = chotels[index]
            index += 1
            self.index = index
            return item
        except IndexError:
            raise StopIteration

    def nearest(self, longitude, latitude, km_radius=EARTH_EQUAT_RADIUS*2):
        """Find the nearest carrier hotel that's within a given radius in km."""
        point = ll_to_xyz(latitude, longitude)
        max_dist = km_radius
        chotel = None
        for ch in self.chotels:
            dist = distance_km(point, ch['xyz'])
            if dist < max_dist:
                #print ch['id'], ch['long'], ch['lat'], dist, max_dist
                max_dist = dist
                chotel = ch
        return chotel
        
    def all_within_by_id (self, longitude, latitude, km_radius=EARTH_EQUAT_RADIUS*2):
        """ Create a dict of carrier hotels within a given radius,
            sorted by carrier-hotel id."""
        chotel_list = self.all_within (longitude, latitude, km_radius)

        chotel_dict = {}
        for chotel in chotel_list:
            chotel_dict[chotel['id']] = chotel

        return chotel_dict

    def all_within (self, longitude, latitude, km_radius=EARTH_EQUAT_RADIUS*2, set_to_render=False):
        """Create a list of carrier hotels within a given radius in km."""
        try:
            point = ll_to_xyz(latitude, longitude)
        except ValueError:
            return []

        chotel = None
        chotel_tuple_list = [ ]

        # --- Create list of chotels within radius ---
        for ch in self.chotels:
            dist = ixmaps.distance_km (point, ch['xyz'] )
            if dist < km_radius:
                chotel_tuple_list.append ( (dist, ch) )

        # --- Sort chotels list ---
        chotel_tuple_list.sort ( )

        # --- Convert to non-tupple by removing distance meta-info ---
        chotel_list = [ ]
        for ch in chotel_tuple_list:
            chotel_list.append (ch[1])

        # --- Set whether to render ---
        for ch in chotel_list:
            if set_to_render:
                ch['networks'] = ''
                # ch['to_render'] = True

        # print chotel_list

        return chotel_list

    def get_type (self, type):
        chotel_list = []

        for chotel in self.chotels:
            if chotel['type'] == type:
                chotel_list.append(chotel)

        return chotel_list

    def get_all (self):
        chotel_list = []

        for chotel in self.chotels:
            chotel_list.append(chotel)

        return chotel_list

class xml_utils:
    def __init__ (self, initial_indent=0):
        self.stack = []
        self.endline = "\n"
        self.initial_indent = initial_indent

    def tag(self, tag_plus_attr):
        if tag_plus_attr[0] == "/":
            raise ValueError
        
        full_tag = self.indent("<" + tag_plus_attr + ">")
        tag = re.sub (RE_XMLTAG, r"\1", tag_plus_attr)

        self.stack.append (str(tag))
        return full_tag + self.endline

    def empty_tag (self, *args):

        number_of_tags = len(args)

        tag_plus_attr = []
        for tag in args:
            tag_plus_attr.append (tag)

        ret_val = ''

        for index in range (0, number_of_tags):

            if tag_plus_attr[index][0] == "/":
                raise ValueError
            full_tag = ("<" + tag_plus_attr[index] + "/>" ) 
            ret_val += full_tag

        ret_val = self.indent (ret_val) + self.endline
        return ret_val

    def end_tag(self, tag=None):
        item = self.stack[-1]
        if (tag):
            if (tag[0] == "/"):
                tag = tag[1:]

        if ((tag != None) and (item != tag)):
            raise ValueError

        else:
            self.stack.pop()
            return self.indent("</" + item + ">") + self.endline

    def stack_size(self):
        return (len (self.stack))

    def get_indent_level (self):
        return self.stack_size ( ) + self.initial_indent

    def indent (self, text, extra=0, endline=False):
        text = str(text)

        ind = self.stack_size()
        indent_increment = "  " 

        new_text = re.sub (RE_NOTEMPTYLINE, indent_increment * (ind+extra+self.initial_indent), text)
        if endline: new_text += self.endline
        return new_text

    def text (self, text=""):
        if (text != '' and text != None):
            return self.indent (text) + self.endline
        else:
            return self.endline

    def text_cont_line (self, text):
        if (text != '' and text != None):
            return self.indent (text) 
        else:
            return ''

    # def tagged_text (self, tag_plus_attr, text):
    def tagged_text (self, *args):

        number_of_tags = len(args) - 1

        text = str(args[-1])

        full_tag = [[]] * number_of_tags
        end_tag =  [[]] * number_of_tags

        for index in range (number_of_tags):
            tag_plus_attr = args[index]
            full_tag[index] = self.indent("<" + tag_plus_attr + ">") 
            if (index > 0):
                full_tag[index] = re.sub (r"^ *", " ", full_tag[index])

            end_tag[index] =  ("</" + re.sub (RE_XMLTAG, r"\1", 
                                             tag_plus_attr) + ">")
            if (index < number_of_tags):
                end_tag[index] += " "


        # text = str(text)
        # full_tag = self.indent("<" + tag_plus_attr + ">")
        # end_tag = "</" + re.sub (RE_XMLTAG, r"\1", tag_plus_attr) + ">"

        ret_val = ''

        for tag in full_tag:
            ret_val += tag

        ret_val += text

        for index in range (number_of_tags-1, -1, -1):
            ret_val += end_tag[index]

        ret_val += self.endline

        return ret_val
        # return full_tag + text + end_tag + self.endline

    def comment (self, comment_tag):
        full_tag = "<!-- " + comment_tag + " -->" 
        return self.indent (full_tag) + self.endline

    def cdata (self, text, indent=True):
        if indent:
            full_text = (self.indent ("<![CDATA[") 
                         + "\n"
                         + self.indent (text, extra=1) + "\n" 
                         + self.indent ("]]>"))

        else:
            full_text = (self.indent("<![CDATA[")
                         + text + "]]>" ) 

        return full_text + self.endline

def URL_encode_ampersands(url):
    return "&amp;".join(url.split("&"))
        
def facility_icons():
    icons = {
    'AGF'         : { 'id': 'AGF',         'symbol': 'google',           'facility': '<b>Google facility</b> located in' },
    'nearAGF'     : { 'id': 'nearAGF',     'symbol': 'neargoogle',       'facility': 'Near a Google facility' },
    'CAN'         : { 'id': 'CAN',         'symbol': 'locationcircle',   'facility': 'In Canada' },
    'NSA1'        : { 'id': 'NSA1',        'symbol': 'nsahigh',          'facility': '<img src="http://ixmaps.ischool.utoronto.ca/ge/nsahigh.png" alt="Legend not found"/></br> <b>Known NSA listening post</b> located at' },
    'NSA2'        : { 'id': 'NSA2',        'symbol': 'nsamedium',        'facility': '<b>Likely NSA listening post</b> located in' },
    'NSA3'        : { 'id': 'NSA3',        'symbol': 'nsalow',           'facility': '<b>Possible NSA listening post</b> located in' },
    'CRG'         : { 'id': 'CRG',         'symbol': 'crg',              'facility': 'Owned by Carlyle Real Estate - CoreSite' },
    'nearCRG'     : { 'id': 'nearCRG',     'symbol': 'nearcrg',          'facility': 'Near a facility owned by Carlyle Real Estate - CoreSite' },
    'INT'         : { 'id': 'INT',         'symbol': 'locationcircle',   'facility': '<b>Router</b> located in' },
    'router_1'    : { 'id': 'router_1',    'symbol': 'router_1',         'facility': '<b>Router</b> located in' },
    'router_3'    : { 'id': 'router_3',    'symbol': 'router_3',         'facility': '<b>Router</b> located in' },
    'router_4'    : { 'id': 'router_4',    'symbol': 'router_4',         'facility': '<b>Router</b> located in' },
    'router_other': { 'id': 'router_other','symbol': 'router_4',         'facility': '<b>Router</b> located in' },
    'chotel'      : { 'id': 'chotel',      'symbol': 'carrierhotel',     'facility': '<b>Carrier hotel</b> located at' },
    'UC'          : { 'id': 'UC',          'symbol': 'undersea',         'facility': '<b>Undersea cable landing site</b> located in' },
    'OTH'         : { 'id': 'OTH',         'symbol': 'locationcircle',   'facility': 'Router' },  # other (is this ever used in the current setup?)
        }
    return icons

def get_ch_class(chotel):
    """Determine styling class for a carrier hotel."""

    if chotel['type'] == 'NSA':
        if chotel['nsa'] == 'A': 
            ixclass = 'NSA1'
        elif chotel['nsa'] == 'B':
            ixclass = 'NSA2'
        else:
            ixclass = 'NSA3'

    elif chotel['type'] == 'UC':
        ixclass = 'UC'

    elif chotel['type'] == 'Google':
	ixclass = 'AGF'

    elif chotel['type'] == 'CH':
        ixclass = 'chotel'

    else:
        ixclass = 'OTH'
    return ixclass

def define_table(conn, tab_name, cols, comment=None, drop_options=""):
    # create a table from scratch with comments
    conn.query("drop table if exists %s %s" % (tab_name, drop_options))
    conn.query(("create table %s (" % tab_name )+(",".join(cols.keys()))+")")
    if comment:
        conn.query("comment on table %s is '%s'" % (tab_name, comment))
    for k in cols:
        col_name = k.split(' ')[0]
        conn.query("comment on column %s.%s is '%s'" % (tab_name, col_name, cols[k]))
    conn.query("grant select on %s to public" % tab_name)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# used by  arin_whois.py  and  set_addr_info.py

class MutexFile(object):
    def __init__(self, lock_file):
        self.lock_file = "/var/run/ixmaps/"+lock_file
        self.fd = None

    def acquire(self):
        # We assume that we have the required file-system permissions
        # which will be true if running as the ixmaps user
        try:
            self.fd = os.open(self.lock_file, os.O_CREAT|os.O_EXCL|os.O_RDWR)
            os.write(self.fd, "%d" % os.getpid())
            return True
        except OSError:
            self.fd = None
        return False

    def release(self):
        if self.fd:
            try:
                os.close(self.fd)
                os.unlink(self.lock_file)
                return True
            except OSError:
                pass
        return False

    def __del__(self):
        self.release()



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# get_range_id used by  arin_whois.py

def get_range_id(conn, addr):
    #print "get_range_id for %s" % addr
    qres = conn.query("select * from ipv4_addr_cidr where net >>= inet('%s')" % addr)
    dr = qres.dictresult()
    try:
        rid = dr[0]['range_id']
    except IndexError:
        rid = None
    return rid

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ASNumSockLookup(object):
    def __init__(self, query_mode="A"):
        pid = os.getpid()
        self.sock_filename = "/tmp/aslook-%d.sock" % pid
        self.query_mode = query_mode;
        try:
            os.remove(self.sock_filename)
        except OSError:
            pass
        self.gs = socket(AF_UNIX, SOCK_DGRAM, 0)
        self.gs.bind(self.sock_filename)

    def query_dquad(self, dquad):
        self.gs.sendto(self.query_mode+dquad, ASNumSockLookup.MM_SOCKET)
        buf = self.gs.recv(128)
        return (buf, 0, 0, 0)

    def __del__(self):
        self.gs.close()
        os.remove(self.sock_filename)
    
    MM_SOCKET = "/tmp/ASNLookup.sock"


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def ll_to_xyz(lat, long):
    if lat == '':
        lat = 0
    if long == '':
        long = 0

    lat_radians = math.pi * float(lat) / 180.0
    long_radians = math.pi * float(long) / 180.0
    x = EARTH_MEAN_RADIUS * math.cos(long_radians) * math.cos(lat_radians)
    y = EARTH_MEAN_RADIUS * math.sin(long_radians) * math.cos(lat_radians)
    z = EARTH_MEAN_RADIUS * math.sin(lat_radians)
    return (x,y,z)

def km_to_degrees(km, lat, scale=1.0):
    deg_lat = scale*km*180.0/(EARTH_MEAN_RADIUS*math.pi)
    deg_long = deg_lat / math.cos(math.pi*lat/180.0)
    return (deg_lat, deg_long)

def distance_km(pos1, pos2):
    dx = pos2[0]-pos1[0]
    dy = pos2[1]-pos1[1]
    dz = pos2[2]-pos1[2]
    return math.sqrt(dx*dx+dy*dy+dz*dz)

def ll_line_to_km (ll1, ll2):
    pos1 = ll_to_xyz (ll1[0], ll1[1])
    pos2 = ll_to_xyz (ll2[0], ll2[1])
    return distance_km (pos1, pos2)

def dist_unit_to_km(s):
    """What to multiply a distance measurement in the unit size to get km."""
    factor = 1.0
    if s == 'm':
        factor = 0.001
    elif s == 'mi':
        factor = 1.609344
    elif s == 'ft':
        factor = 0.0003048
    return factor

MILE_TO_KM = 1.609344

    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def sanitize_str(s):
    safe_chars = " !$*+,-./0123456789:=?ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
    try:
        return ''.join(filter(lambda x: x in safe_chars, [c for c in s]))
    except TypeError:
        return ''

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def dq_to_num(dq):
    """convert dotted-quad IPv4 address string to integer."""
    dqa = [int(s) for s in dq.split(".")]
    return 16777216*dqa[0] + 65536*dqa[1] + 256*dqa[2] + dqa[3]

def num_to_dq(num):
    """convert integer to dotted-quad IPv4 address string"""
    dqa = [(0xff&(num>>i)) for i in range(24,-1,-8)]
    return '.'.join([str(i) for i in dqa])


# algorithm from: http://www.perlmonks.org/?node_id=79659

def nr_to_cidr(nMin, nMax):
    """convert network address range to one or more CIDR blocks."""
    # CIDR = Classless Inter-domain Routing, see RFC4632 section 3.1
    plist=[]
    bitsMin=1
    maskMin=1
    bitsMax=1
    maskMax=1
    while True:
        while 0 == (nMin & maskMin):
            maskMin <<= 1
            maskMin |= 1
            bitsMin += 1
        if nMax < ( nMin | maskMin ):
            break
        plist.append((nMin, 33-bitsMin))
        nMin |= maskMin
        nMin += 1
    while True:
        while maskMax == ( nMax & maskMax ):
            maskMax <<= 1
            maskMax += 1
            bitsMax += 1
        nMax &= ~maskMax
        if nMax < nMin:
            break
        plist.append((nMax, 33-bitsMax))
        nMax -= 1
    plist.sort()
    return plist

def get_traceroute(conn, id):
    qres = conn.query("select * from traceroute where id=%d" % id)
    try:
        id = qres.dictresult()[0]['id']
    except IndexError:
        raise TracerouteException, "failed to find traceroute %d" % id
    return qres.dictresult()[0]


def get_tr_items (conn, id):
    qres = conn.query ("select * from tr_item where traceroute_id=%d order by hop, attempt" % id)
    try:
        id = qres.dictresult()[0]['traceroute_id']
    except IndexError:
        raise TracerouteException, "failed to find traceroute items for %d" % id
    return qres.dictresult()

def get_tr_items_dim(da):
    """da is array of dicts, each dict representing a single traceroute probe"""
    nhops = nattempts = 0
    for d in da:
        if d['attempt'] > nattempts:
            nattempts = d['attempt']
        if d['hop'] > nhops:
            nhops = d['hop']
    return (nhops, nattempts)


# ?? can this be part of get_route_hops()?

def get_available_ip_addresses (route_hop_attempts): 
    address_list = []
    last_successful_hop = 0

    # --- Save first successful attempt (of 4) for each hop ---
    for item in route_hop_attempts:
        if item['hop'] != last_successful_hop:
            hop = item['hop']
            addr = item['ip_addr']

            if (hop > len(address_list)):
                address_list.append (None)

            if is_valid_ip(addr):
                address_list[hop-1] = addr
                last_successful_hop = hop

    return address_list

def get_ip_info (conn, ip_list, with_isp=False):
    # print "IP: " + str(addr)

    addr = ''
    for address in ip_list:
        if address:
            addr += "ip_addr='" + address + "' "

    addr = re.sub (r"(\.[0-9]+') (ip_addr=')", r'\1 or \2', addr)
    addr = '(' + addr + ')'

    if not with_isp:
        qres = conn.query("select * from ip_addr_info where %s" % addr) 
    else:
        addr += ' and (num = asnum)'
        qres = conn.query("select * from ip_addr_info,as_users where %s" % addr) 
        

    ip_details = qres.dictresult ( )

    ip_dict = { }

    for d in ip_details:
        # d['ip_addr'] = addr

        ip = d['ip_addr']

        ip_dict[ip] = {}

        ip_dict[ip]['ip_addr'] = ip
        ip_dict[ip]['hostname'] = str(d['hostname'])
        ip_dict[ip]['lat'] = str(d['lat'])
        ip_dict[ip]['long'] = str(d['long'])
        ip_dict[ip]['asnum'] = str(d['asnum'])
        ip_dict[ip]['country'] = str(d['mm_country'])
        ip_dict[ip]['region'] = str(d['mm_region'])
        ip_dict[ip]['city'] = str(d['mm_city'])
        ip_dict[ip]['pcode'] = str(d['mm_postal'])
        ip_dict[ip]['area_code'] = str(d['mm_area_code'])
        ip_dict[ip]['dma_code'] = str(d['mm_dma_code'])
        ip_dict[ip]['override'] = str(d['gl_override'])

        if 'name' in d:
            ip_dict[ip]['name'] = str(d['name'])

        if ip_dict[ip]['override']:

            #this is a little different than tr-detail, maybe FIX?
            lat_digits = len(str(d['lat'])) - str(d['lat']).find('.') - 1
            long_digits = len(str(d['long'])) - str(d['long']).find('.') - 1
            if lat_digits >= 5 or long_digits >= 5:
                ip_dict[ip]['geo_precision'] = 'building level'
            elif lat_digits <= 2 or long_digits <= 2:
                ip_dict[ip]['geo_precision'] = 'city level'
            else:
                ip_dict[ip]['geo_precision'] = 'Maxmind'
        
    return ip_dict

def get_route_hops (route_hop_attempts, conn):
    # print ("route_hop_attempts:", len(route_hop_attempts))
    nhops = get_available_hops(route_hop_attempts)
    ip_list = get_available_ip_addresses(route_hop_attempts)

    coords = []

    # --- Get route-info on each hop ---
    for i in range(len(ip_list)):
        addr = ip_list[i]
        ip_addr_info = ixmaps.get_ip_addr_info(conn, addr)

        coords.append (ip_addr_info)
        if len(ip_addr_info['long']) != 0 or len(ip_addr_info['lat']) != 0:
            try:
                if (not is_valid_coord(ip_addr_info['long'], ip_addr_info['lat'])):
                    ip_addr_info['long'] = None
                    ip_addr_info['lat'] = None
            except ValueError:
                    ip_addr_info['long'] = None
                    ip_addr_info['lat'] = None
    last_hop = 0

    for i in range(len(route_hop_attempts) ):
        hop_attempt = route_hop_attempts[i]
        # print '\n\n\n\nhop_attempt (i):' , i
        # print hop_attempt

        hop = hop_attempt['hop']
        if (hop != last_hop):
            # print "\n\n\n\nhop-1:", hop-1
            # print "len(coords)", len(coords)
            # print ("len(route_hop_attempts):", len(route_hop_attempts),
                   # ", i:", i)
            # print hop_attempt
            coords[hop-1]['rtt'] = []
            last_hop = hop

        else:
            attempt = hop_attempt['attempt']
            # print "len: ", coords[hop-1]['rtt_ms'], attempt
            coords[hop-1]['rtt'].insert(len(coords[hop-1]['rtt']),
                                    hop_attempt['rtt_ms'] )

            # print "coords:", coords

            # -- IPs must be strings ---
            for hop in coords:
                # print "hop: ", hop
                if hop['ip_addr'] == None:
                    hop['ip_addr'] = ''

    return coords

def is_valid_ip (ip): 
    if not ip:
        ip = ''
    if (re.match (r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*$', ip) ):
        return True
    else:
        return False    

def is_valid_coord(longitude, latitude):
    """Reject invalid coordinates too close to "placeholder" coordinates.
    
    These are: 0,0  in Atlantic off of Africa
               -95,60  near shore of Hudson's Bay, used by MaxMind for unknown in Canada
               -97.38  a field in Kansas, used by MaxMind for unknown in US"""

    if ((longitude == None)
    or (longitude == '')
    or (latitude == None)
    or (latitude == '')):
        return False

    bad_coords = [(0.0,0.0), (-95.0,60.0), (-97.0,38.0)]
    point2=(float(longitude), float(latitude))
    for c in bad_coords:
        if within(c, point2, 0.0001):
            return False
    return True

def within(point1, point2, dist):
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]
    dist_squared = dx*dx + dy*dy
    return dist_squared < dist*dist

def get_available_hops(da):
    hop = -1
 
    for d in da:
        try:
            if d['hop'] > hop:
                hop = d['hop'] 
        except KeyError:
            pass
    return hop
	
def get_ip_addr_info (conn, addr):
    # print "IP: " + str(addr)

    if addr:
        # print "addr: " + str(addr)
        qres = conn.query("select * from ip_addr_info where ip_addr='%s'" % addr)
        d = qres.dictresult()[0]
        d['lat'] = str(d['lat'])
        d['long'] = str(d['long'])
        d['hostname'] = str(d['hostname'])
        d['asnum'] = str(d['asnum'])
        d['city'] = str(d['mm_city'])
        d['state'] = str(d['mm_region'])
        d['certainty'] = str(d['gl_override'])
        d['country'] = str(d['mm_country'])
        d['region'] = str(d['mm_region'])
        d['pcode'] = str(d['mm_postal'])
        d['area_code'] = str(d['mm_area_code'])
        d['dma_code'] = str(d['mm_dma_code'])
        d['override'] = str(d['gl_override'])
        d['ip_addr'] = addr

    else:
        d={'lat': '', 'hostname': '', 'ip_addr': None, 'long': '', 'asnum': '',
           'region': '', 'city': '', 'country': '', 'pcode': '', 'area_code': '', 'dma_code': '', 'override': ''}
        
    return d

def is_nsa (ipInfo=None, ip=None, conn=None, long_lat=None):
    
    if get_nsa_class (ipInfo, ip, conn, long_lat):
        return True
    else:
        return False

def get_nsa_class (ipInfo=None, ip=None, conn=None, long_lat=None):
    
    if long_lat:
        (longitude, latitude) = long_lat

    else:
        if not ipInfo:
            ipInfo = get_ip_addr_info (ip, conn)

        longitude = ipInfo['long']
        latitude = ipInfo['lat']

    if not conn:
        conn = ixmaps.DBConnect.getConnection()

    all_chotels = ixmaps.CHotels(conn)
    chotels_in_city_list = all_chotels.all_within (longitude, latitude, 
                                                   MAX_NSA_DIST)
    chotels_in_city = ixmaps.CHotels (chotels=chotels_in_city_list)
    nsa_posts_in_city_list = chotels_in_city.get_type('NSA')
    

    # chotel = all_chotels.nsa_in_city (float(longitude), float(latitude),
                                      # (MAX_CHOTEL_DIST*20))

    if not nsa_posts_in_city_list:
        nsa_type = None

    else:
        nsa_type = 'Z'
        for nsa in nsa_posts_in_city_list:
            if ( ord(nsa['nsa']) < ord(nsa_type) ):
                nsa_type = nsa['nsa']

    return nsa_type

def get_country (ipInfo=None, ip=None, conn=None):

    if not ipInfo:
        ipInfo = get_ip_addr_info (ip, conn)
        
    country = ipInfo['country']

    return country

def is_chotel (ipInfo=None, ip=None, conn=None, long_lat=None):
    
    if long_lat:
        (longitude, latitude) = long_lat

    else:
        if not ipInfo:
            ipInfo = get_ip_addr_info (ip, conn)

        longitude = ipInfo['long']
        latitude = ipInfo['lat']

    if not conn:
        conn = ixmaps.DBConnect.getConnection()

    all_chotels = ixmaps.CHotels(conn)

    try:
        chotel = all_chotels.nearest (float(longitude), float(latitude),
                                      ixmaps.MAX_CHOTEL_DIST)
    except ValueError:
        return False

    if chotel and (chotel['type'] == "CH"):
        return True
    else:
        return False

def html_max_mind_attribution ( ):
    html = xml_utils ( )
    doc = ''

    doc += html.empty_tag ('br')

    doc += html.tag ('p')
    doc += html.text ('This product includes GeoLite data created by MaxMind, available from')
    doc += html.tagged_text ('a href="http://maxmind.com/"', 'maxmind.com.')
    doc += html.end_tag ('/p')

    return doc

def get_ip_addr_info_list(address_list, conn=None):
    if conn == None:
        conn = ixmaps.DBConnect.getConnection()

    if address_list:

        # --- Generate SQL query ---
        addresses_str = ''
        for address in address_list:
            if address != None:
                if addresses_str != "":
                    addresses_str += ", "
                addresses_str += "'%s'" % (address)
        # print "addresses_str:", addresses_str

        if addresses_str:
            qres = conn.query("select * from ip_addr_info where ip_addr in (%s)"
                              % addresses_str)
        else:
            qres = None
            return []

        #if DEBUG:
        #    print "\nqres: ", qres

        # if len(qres.dictresult()) > 0:

        l = len(qres.dictresult())
        ip_info_list = [None] * l
        for aa in range (0, l):

            d = qres.dictresult()[aa]
            ip_info_list[aa] = {}
            ip_info_list[aa]['lat'] = str(d['lat'])
            ip_info_list[aa]['long'] = str(d['long'])
            ip_info_list[aa]['asnum'] = str(d['asnum'])
            ip_info_list[aa]['country'] = str(d['mm_country'])
            ip_info_list[aa]['region'] = str(d['mm_region'])
            ip_info_list[aa]['city'] = str(d['mm_city'])
            ip_info_list[aa]['pcode'] = str(d['mm_postal'])
            ip_info_list[aa]['area_code'] = str(d['mm_area_code'])
            ip_info_list[aa]['dma_code'] = str(d['mm_dma_code'])
            ip_info_list[aa]['ip_addr'] = d['ip_addr']
            ip_info_list[aa]['hostname'] = d['hostname']
            #ip_info_list[aa]['type'] = d['type']

    if (not address_list) or (len(qres.dictresult())==0):
        ip_info_list=[{'lat': '', 'hostname': '', 'ip_addr': None, 'long': '',
           'asnum': '', 'region': '', 'city': '', 'country': '',
           'pcode': '', 'area_code': '', 'dma_code': ''}]
    return ip_info_list



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__ == '__main__':
    import sys
    
    a1=dq_to_num(sys.argv[1])
    a2=dq_to_num(sys.argv[2])
    
    pl=nr_to_cidr(a1, a2)
    for p in pl:
        print "%s/%d" % (num_to_dq(p[0]), p[1])
        
# original code from: http://www.perlmonks.org/?node_id=79659

#!/usr/bin/perl -w
#
# use strict;
# 
# sub output {
#     my( $nLow, $cBits )= @_;
#     my $ipLow= join ".", unpack "C*", pack "N", $nLow;
#     print "    $ipLow/$cBits\n";
# }
# 
# while(  <DATA>  ) {
#     my( $ipMin, $ipMax )= split " ", $_;
#     print "$ipMin - $ipMax:\n";
#     my $nMin= unpack "N", pack "C*", split /\./, $ipMin;
#     my $nMax= unpack "N", pack "C*", split /\./, $ipMax;
#     my $bitsMin= 1;
#     my $maskMin= 1;
#     my $bitsMax= 1;
#     my $maskMax= 1;
#     while( 1 ) {
#         while(  0 == ( $nMin & $maskMin )  ) {
#             ( $maskMin <<= 1 ) |= 1;
#             $bitsMin++;
#         }
#         last   if  $nMax < ( $nMin | $maskMin );
#         output( $nMin, $bitsMin-1 );
#         ( $nMin |= $maskMin ) += 1;
#     }
#     while( 1 ) {
#         while(  $maskMax == ( $nMax & $maskMax )  ) {
#             ( $maskMax <<= 1 ) |= 1;
#             $bitsMax++;
#         }
#         $nMax &= ~$maskMax;
#         last   if  $nMax < $nMin;
#         output( $nMax--, $bitsMax-1 );
#     }
# }
# __END__
# 192.168.0.0 192.168.255.255
# 192.168.1.17 192.168.112.26
