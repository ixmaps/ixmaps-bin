#!/usr/bin/python
import os
import sys
import pg
import subprocess
from ixmaps import DBConnect

conn = DBConnect.getConnection()
result = conn.query("select COUNT(ip_addr) from ip_addr_info where p_status = 'G'")

for tot in result.getresult() :
		tot_new_ips = tot[0]

print tot_new_ips

if tot_new_ips != 0:
	print "Calling geocorrection script..."
	#os.system("/Users/antonio/mywebapps/ixmaps.ca/bin.anto/test.sh")
	#os.system("/home/ixmaps/scripts/corr-latlong.sh")
	#subprocess.Popen("/home/ixmaps/scripts/corr-latlong.sh", shell=True, executable='/bin/bash')
	#subprocess.call("/home/ixmaps/scripts/corr-latlong.sh")
	#subprocess.check_call(['/home/ixmaps/scripts/testycat.sh', '-v'])
	subprocess.Popen(['/home/ixmaps/scripts/corr-latlong.sh -g'], shell = True)
else:
	print "Nothing to do..."
