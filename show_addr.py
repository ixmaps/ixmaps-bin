#!/usr/bin/python

"""
Utility program to show rows from the ip_addr_info table.

When invoked without any arguments, all entries are shown.
Any arguments are IPv4 addresses expressed as dotted-quads.

The results are in Python dictionary format.
"""

import pg
import time
import sys

class DBConnect(object):
    conn = None
    def getConnection():
        if not DBConnect.conn:
            DBConnect.conn = pg.connect("ixmaps", "localhost", 5432)
        return DBConnect.conn
    getConnection = staticmethod(getConnection)

def get_ip_addr_info(conn, addr):
    qres = conn.query("select * from ip_addr_info where ip_addr='%s'" % addr)
    return qres.dictresult()[0]

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
    try:
        ai = get_ip_addr_info(conn, addr)
    except IndexError:
        ai = "not found"
    print addr, ai

