#!/usr/bin/python

"""
Transitional program to rename all NULL submitter
names to "not@specified".  The at-sign (@) is not
a valid character for submission.

The tr-gather.cgi program has been modified to set
NULL names to this value.
"""

import pg
import sys
from ixmaps import DBConnect

def update_null_subs(conn):
    qres = conn.query("update traceroute set submitter='not@specified' where submitter=''")

conn = DBConnect.getConnection()

update_null_subs(conn)

