#!/usr/bin/python

# transitional script to change incorrect AS numbers

# The iPlane data that was originally used contained
# bogus "reasonable default" announcements.  The 
# RouteViews data does not have this "feature".

# edit this variable to either True or False
do_update=True
#
######################################################

from ixmaps import ASNumSockLookup,DBConnect

def update_asn(conn, ip_addr, rv_asn):
    conn.query("update ip_addr_info set asnum=%d where ip_addr='%s'" % (rv_asn, ip_addr))

al = ASNumSockLookup("A")

conn = DBConnect.getConnection()

dr = conn.query("select ip_addr,asnum,p_status from ip_addr_info").dictresult()


diff_count = 0
for d in dr:
    rv_asn = int(al.query_dquad(d['ip_addr'])[0])
    if rv_asn != d['asnum']:
        print "%(ip_addr)s %(asnum)d s=%(p_status)s" % d,
        print rv_asn
        diff_count += 1
        if do_update:
            update_asn(conn, d['ip_addr'], rv_asn)
print "%d IPv4 addrs, %d differing ASnums" % (len(dr), diff_count)
