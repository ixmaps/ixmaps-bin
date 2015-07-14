#!/usr/bin/python

"""
Transitional program to populate the ip_addr_info table.

Arguments are dotted-quad IPv4 addresses.  If none are
given, the tr_item is scanned for addresses that have not
been entered as of yet into the ip_addr_info table.

The tr-gather.cgi program has been modified to insert
entries into the table.  Previously, this was not done,
therefore the need for this program.
"""

import pg
import time
import sys
from ixmaps import DBConnect

def ip_addr_present(conn, addr):
    qres = conn.query("select count(*) from ip_addr_info where ip_addr='%s'" % addr)
    return qres.dictresult()[0]['count'] == 1

def new_ip_addr(conn, addr):
    qres = conn.query("insert into ip_addr_info (ip_addr) values ('%s')" % addr)

def get_available_ip_addrs(conn):
    qres = conn.query("select distinct ip_addr from tr_item")
    return [d['ip_addr'] for d in qres.dictresult()]

conn = DBConnect.getConnection()

addrs = sys.argv[1:]
if len(addrs) == 0:
    addrs = get_available_ip_addrs(conn)
for addr in addrs:
    if not addr:
        continue
    present = ip_addr_present(conn, addr)
    print addr, present
    if not present:
        new_ip_addr(conn, addr)

