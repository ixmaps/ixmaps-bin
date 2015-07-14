#!/usr/bin/python

# Test UNIX-domain socket connection to MaxMind query daemon.
# Command line arguments are a one-letter query mode preceeded by '-'
# and an IPv4 address.  Both are optional.

import socket
from socket import socket, AF_INET, AF_UNIX, SOCK_DGRAM
import os
import sys

MM_SOCKET = "/tmp/MaxMind-GLC.sock"
mode = 'L'
ip_addr = '4.11.231.171'

pid = os.getpid()
GL_SOCKET = "/tmp/geoloc-%d.sock" % pid

try:
    os.remove(GL_SOCKET)
except OSError:
    pass

args = sys.argv[1:]
try:
    if args[0][0] == '-':
        mode = args[0][1]
        args = args[1:]
except IndexError:
    pass

try:
    ip_addr = args[0]
except IndexError:
    pass

#print mode, ip_addr
   

gs = socket(AF_UNIX, SOCK_DGRAM, 0)
gs.bind(GL_SOCKET)

gs.sendto(mode+ip_addr, MM_SOCKET)
buf = gs.recv(128)
print buf
gs.close()
os.remove(GL_SOCKET)
