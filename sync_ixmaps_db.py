#!/usr/bin/python

# This script downloads posgress latest database from www.ixmaps.ca and updates local database

import cgi
import mechanize
import os
import urllib

SQL_LOCAL_PATH = "/home/ixmaps/backup_remote"
SQL_REMOTE_URL = "http://www.ixmaps.ca/dumps/download_sql.php"
#SQL_REMOTE_URL = "https://www.ixmaps.ca/dumps/download_sql.php"

browser = mechanize.Browser()
response = browser.open(SQL_REMOTE_URL)
info = response.info()
header = info.getheader('Content-Disposition')

value, params = cgi.parse_header(header)

print "***********************************"
print "Downloading " +  params['filename'] + " ..."

fileName = SQL_LOCAL_PATH + "/" + params['filename']
fileName1 = params['filename']
tempName =  fileName1.split('.', 1)
baseName = tempName[0]

urllib.urlretrieve ("http://www.ixmaps.ca/dumps/download_sql.php", fileName)
print "***********************************"
print "Backup downloaded: " + SQL_LOCAL_PATH + "/" + params['filename']
print "***********************************"
print "Extracting file..."
os.system('gunzip -c ' + fileName + ' > ' + SQL_LOCAL_PATH + '/' + baseName + '.sql')
print "File " + baseName+ ".sql extracted"
print "***********************************"
print "Cleaning IXmaps Local database ..."
os.system('psql -d ixmaps -f /home/ixmaps/backup_remote/drop_schema.sql')
print "***********************************"
print "Updating IXmaps Local database ..."
os.system('psql -d ixmaps -f /home/ixmaps/backup_remote/' + baseName + ".sql")
print "***********************************"
print "Import completed: " + baseName + ".sql"
print "***********************************"
print "Deleting sql file " + baseName+ ".sql ..."
os.system('rm /home/ixmaps/backup_remote/' + baseName + ".sql")
print "***********************************"
print "Update of IXmaps database in the clone server is completed !"
print "***********************************"
