#!/usr/bin/python

# parse the result of a network query to whois.arin.net
#
# these are produced by the query
# whois -h whois.arin.net 'n - <ip-addr>'

# when an IP addr has no known AS#, we have to
# consult whois for some information

#
# three tables
#
# t1: CIDR IPv4 address blocks resolved via whois (ipv4_addr_cidr)
#    net            primary key is CIDR  
#    range_id       foreign key refs t3
# this table is always checked first if an IP addr has no AS#
# when a row is added to the address block table, all of the
# contained CIDR blocks (usually just one) are added here
# probably only the most specific network should be added here

# t2: request table (ipv4_whois_req)
#    ip_addr        IPv4 addr unannounced in originAS prefix by BGP
#    rir            Regional Internet Registry handling the enclosing IPv4 address space
#    ntries         Number of whois retries for this address
#    last_try       Seconds since Epoch of the last try
#    status         New, name Resolution fail, Connection fail, Empty reply, '0-9' records found
#    id             Request ID is referred by ipv4_addr_range.req_id
# a row is added if an IP address without a known originAS is found
# for now, only query ARIN
# a daemon checks every minute to see if there are any outstanding requests
# use exponential backoff on failures

# t3: address block table (ipv4_addr_range)
#    first          1st address
#    last           last address
#    org_name       ARIN's OrgName
#    net_name       ARIN's NetName
#    net_handle     ARIN's NetHandle
#    asnum          imputed AS# (may be -1)
#    genericness    0 for most specific network returned, >0 for more generic (larger enclosing) networks
#    id             addr_blockID
#    req_id         requestID in the ipv4_whois_req table
# when a request has a satisfactory outcome, all of it's networks are added here



import sys
import os
import time
import string
from ixmaps import dq_to_num, num_to_dq, nr_to_cidr, DBConnect, get_range_id, MutexFile
import socket
import getopt
import pg

WHOIS_SERVER="whois.arin.net"

# A lock file is used to protect one invocation of this program doing request processing
# (using the -c argument) from another.  As queued request processing is triggered by
# a periodic cron job, we don't proceed with a new request processing if the previous
# is incomplete.
LOCK_FILE="arin-whois.lock"


def whois_request(server, addr, port=43):
    """do a summary network address space request"""
    status='S'
    resp=''
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))
        sock.sendall("n - %s\r\n" % addr)
        resp = sock.recv(8192)
        sock.close()
    except socket.error:
        status = 'C'
    except socket.gaierror:
        status = 'R'
    if status == 'S' and len(resp) == 0:
        status = 'E'
    return (status, resp)

def responsible_rir(conn, prefix):
    qres = conn.query("select * from iana_ipv4_alloc where prefix >>= inet('%s')" % prefix)
    dr = qres.dictresult()
    try:
        rir = dr[0]['whois']
        if not rir and dr[0]['status'] == 'LEGACY':
            rir = 'arin'
    except IndexError:
        rir = ''
    if rir[:6] == 'whois.':
        rir=rir[6:]
    if rir[-4:] == '.net':
        rir=rir[:-4]
    return rir

def get_request_id(conn, addr):
    qres = conn.query("select * from ipv4_whois_req where ip_addr = inet('%s')" % addr)
    dr = qres.dictresult()
    try:
        rid = dr[0]['id']
    except IndexError:
        rid = None
    return rid

def get_requests_by_status(conn, req_status):
    """retrieve requests by status codes limited by count."""
    status = '|'.join([c for c in req_status])
    qres = conn.query("select * from ipv4_whois_req where rir='arin' and status ~ '%s' order by last_try" % status)
    dr = qres.dictresult()
    return dr

def not_back_off(d, my_time, verbose=False):
    BACKOFF_SCHED_QUANTUM=60
    delay=BACKOFF_SCHED_QUANTUM*2**(d['ntries']-1)
    if verbose:
        print "not_back_off(%s, %d)" % (str(d), my_time)
    return my_time >= d['last_try']+int(delay)

def get_requests(conn, max_req, verbose):
    # try for records with status any of: New, name Resolution failed, Connection failure
    dr = get_requests_by_status(conn, "NRC")
    my_time = long(time.time())
    dr = [d for d in dr if not_back_off(d, my_time, verbose) and d['rir'] == 'arin']
    if len(dr) < max_req:
        # Empty results (assuming that this is a temporary situation)
        dr_e = [d for d in get_requests_by_status(conn, "E") if not_back_off(d, my_time, verbose)]
        dr += dr_e
    dr = dr[:max_req]
    if verbose:
        print dr
    return [WhoisRequest(conn, verbose=verbose).set_from_dict(d) for d in dr]

class WhoisRequest(object):
    def __init__(self, conn, ip_addr=None, rir=None, verbose=False):
        self.conn = conn
        self.verbose = verbose
        self.my_time = int(time.time())
        self.parser = NetSummaryParser(self, verbose=verbose)
        self.ip_addr = ip_addr
        self.rir = rir
        self.ntries = 0
        self.last_try = -1
        self.status = 'N'
        self.id = 0

    def set_from_dict(self, d):
        self.status = d['status']
        self.ip_addr = d['ip_addr']
        self.last_try = d['last_try']
        self.rir = d['rir']
        self.ntries = d['ntries']
        self.id = d['id']
        return self

    def update(self):
        """Update the database copy of self."""
        self.ntries += 1
        self.last_try = self.my_time
        vstr=" ('%s', inet('%s'), %d, %d) where id=%d"
        vstr=vstr % (self.status, self.ip_addr, self.last_try, self.ntries, self.id)
        qres = self.conn.query("update ipv4_whois_req set (status, ip_addr, last_try, ntries) = "+vstr)

    def set_id(self, id):
        """set requestID is for testing only."""
        self.id = id

    def new_request(self):
        if self.ip_addr:
            # if a CIDR block has already been learnt, go no farther
            range_id = get_range_id(self.conn, self.ip_addr)
            if range_id:
                print >>sys.stderr, "%s is inside range (ID=%d)" % (self.ip_addr, range_id)
                sys.exit(1)
            # if a whois request is outstanding for this address, toss the request
            req_id = get_request_id(self.conn, self.ip_addr)
            if req_id:
                print >>sys.stderr, "%s is already pending (request ID %d)" % (self.ip_addr, req_id)
                sys.exit(2)
            self.rir = responsible_rir(self.conn, self.ip_addr)
            self.conn.query("insert into ipv4_whois_req (ip_addr, rir) values (inet('%s'), '%s')" % (self.ip_addr, self.rir))

#     IP addr
#     RIR to be queried (for now only do ARIN)
#     ntries
#     tstamp last try
#     status - new request, no connection/response, no name res, empty reply, no records found, records found
#     requestID

    def put_range(self, genericness, OrgName, NetName, NetHandle, range_begin, range_end):
        if not self.conn:
            return 0
        range_id = self.conn.query("select nextval('ipv4_addr_range_id')").dictresult()[0]['nextval']
        fld_names = "first, last, org_name, net_name, net_handle, asnum, genericness, id, req_id"
        vstr = "inet('%s'), inet('%s'), '%s', '%s', '%s', %d, %d, %d, %d"
        vstr = vstr % (range_begin, range_end, OrgName, NetName, NetHandle, -1, genericness, range_id, self.id)
        self.conn.query("insert into ipv4_addr_range (%s) values (%s)" % (fld_names, vstr))
        return range_id

    def put_cidr(self, range_id, pfx, pfx_len):
        if not self.conn:
            return
        if self.verbose:
            print "put_cidr(%d, %s, %d)" % (range_id, pfx, pfx_len)
        try:
            self.conn.query("insert into ipv4_addr_cidr (net, range_id) values (inet('%s/%d'), %d)" % (pfx, pfx_len, range_id))
        except pg.ProgrammingError, e:
            # duplication due to two addresses within same address range
            # two such requests may become outstanding at the same time due to delay
            if str(e).find('duplicate key value violates unique constraint') < 0:
                raise

    def do(self):
        (status, buf) = whois_request("whois.%s.net" % self.rir, self.ip_addr)
        if status == 'S':
            net_count = self.parser.parse_result_buf(buf)
            if net_count > 9:
                net_count = 9
            self.status = "%d" % net_count
        else:
            self.status = status
        self.update()


class NetSummaryParser(object):
    def __init__(self, req, verbose=False):
        self.verbose = verbose
        self.req = req

    def set_req(self, req):
        self.req = req

    def set_verbose(self, verbose):
        self.verbose = verbose

    def parse_line_pair(self, genericness, line1, line2):
        """parse a line pair from a whois network summary query to ARIN.
    
        line1 holds the OrgName, NetName and, in parentheses, NetHandle.
        line2 holds the NetRange preceeded by a run of blanks."""
        l1_parts=string.strip(line1).split(" ")
        net_range=[s for s in line2.split(" ") if len(s) > 1]
        #print l1_parts
        OrgName=" ".join(l1_parts[:-2])
        NetName=l1_parts[-2]
        NetHandle=l1_parts[-1][1:-1]
        if self.verbose:
            print "OrgName=%s NetName=%s NetHandle=%s NetRange=%s - %s" % (OrgName, NetName, NetHandle, net_range[0], net_range[1]) 
        range_id = self.req.put_range(genericness, OrgName, NetName, NetHandle, net_range[0], net_range[1])
        n_start = dq_to_num(net_range[0])
        n_end = dq_to_num(net_range[1])
        #print "%08x %08x" % (n_start, n_end)
        # 108.0.0.0 - 108.57.191.255 is a good example of where we need CIDR
        pl=nr_to_cidr(n_start, n_end)
        for p in pl:
            dquad = num_to_dq(p[0])
            if self.verbose:
                print "CIDR: %s/%d" % (dquad, p[1])
            self.req.put_cidr(range_id, dquad, p[1])
    
    
    def parse_result_lines(self, lines):
        net_count = 0
        for i in range(len(lines)):
            line=lines[i]
            if len(line) == 0:
                continue
            if line[:19] == "No match found for ":
                break
            if line[0] == "#":
                break
            if line[0] != ' ':
                try:
                    net_line=lines[i+1]
                    if net_line[0] == " ":
                        self.parse_line_pair(net_count, line, net_line)
                        net_count += 1
                except IndexError:
                    pass
        return net_count
    
    def parse_result_buf(self, buf):
        lines=buf.split('\n')
        return self.parse_result_lines(lines)
        
    def parse_result_file(self, fname):
        fd=open(fname)
        buf=fd.read()
        fd.close()
        return self.parse_result_buf(buf)
    

def help():
    print """
Use: arin_whois.py [options] [IPaddr]*

Submit a batch of pending requests to the ARIN whois server for summary
information about network address space.

Options:
    -n addr   enter a whois request for IPv4 addr
    -c NN     maximum number of pending requests in the database to process
    -w server use server to query instead of ARIN's whois server
    -f file   use the contents of file as a whois response body (for testing)
    -r reqID  pretend to be this request ID (for testing)
    -v        be verbose
    -h        this help

If none of the -c, -n or -f options are used, any IPv4 addresses on the command line
are used.  Only the -n and -c options cause anything in the database to be changed.

Examples:
arin_whois.py -n 1.2.3.4    # submit a whois request for IP address 1.2.3.4
arin_whois.py -c 4          # process at most 4 outstanding whois requests
    """

progname = sys.argv[0]

try:
    (opts, addrs) = getopt.getopt(sys.argv[1:], "hc:f:w:vr:n:")
except getopt.GetoptError, exc:
    print >>sys.stderr, "%s: %s" % (progname, str(exc))
    sys.exit(1)

db_request_count = 0
request_file=None
whois_server=WHOIS_SERVER
verbose=False
want_db_conn=False
reqID=0
new_req_addr=None
for flag, value in opts:
    if flag == '-h':
        help()
        sys.exit(0)
    elif flag == '-c':
        db_request_count = int(value)
        want_db_conn=True
    elif flag == '-f':
        request_file = value
    elif flag == '-w':
        whois_server = value
    elif flag == '-v':
        verbose=True
    elif flag == '-r':
        reqID = int(value)
    elif flag == '-n':
        new_req_addr = value
        want_db_conn=True

if want_db_conn:
    conn = DBConnect.getConnection()
    print conn

req=WhoisRequest(conn, new_req_addr, verbose=verbose)

# setting the reqID via the command line only makes sense
# when we are not pulling requests from the database
if db_request_count == 0 and reqID != 0:
    req.set_id(id)

parser=NetSummaryParser(req, verbose)

if db_request_count > 0:
    lock=MutexFile(LOCK_FILE)
    if lock.acquire():
        ra = get_requests(conn, db_request_count, verbose)
        if verbose:
            print ra
        for r in ra:
            r.do()
        lock.release()
    else:
        print "cannot acquire lock file"
        sys.exit(0)
elif new_req_addr:
    req.new_request()
elif request_file:
    parser.parse_result_file(request_file)
else:
    for addr in addrs:
        (status, buf) = whois_request(whois_server, addr)
        if status == 'S':
            parser.parse_result_buf(buf)

    
# two sample input files follow (ignore the leading "# ")

# 
# No match found for 128.0.0.0.
# 
# # ARIN WHOIS database, last updated 2010-04-06 20:00
# # Enter ? for additional hints on searching ARIN's WHOIS database.
# #
# # ARIN WHOIS data and services are subject to the Terms of Use
# # available at https://www.arin.net/whois_tou.html

# AT&T Internet Services SBCIS-SIS80 (NET-63-192-0-0-1) 
#                                   63.192.0.0 - 63.207.255.255
# San Francisco Art Institute SBCIS991119051 (NET-63-197-251-0-1) 
#                                   63.197.251.0 - 63.197.251.255
# 
# # ARIN WHOIS database, last updated 2010-04-05 20:00
# # available at https://www.arin.net/whois_tou.html
