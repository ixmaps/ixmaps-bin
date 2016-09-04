#!/usr/bin/python

# This is a new (2015-12-03) script to download maxmind data to be triggered by a cronjob on the first Wed of every month

import urllib
import os

MM_DATA_PATH = "/home/ixmaps/ix-data/mm-data"

os.system("rm %s/GeoIP.dat" % MM_DATA_PATH)
os.system("rm %s/GeoLiteCity.dat" % MM_DATA_PATH)
os.system("rm %s/GeoIPASNum.dat" % MM_DATA_PATH)
os.system("rm %s/GeoLiteCityv6.dat" % MM_DATA_PATH)
urllib.urlretrieve ("http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz",
"%s/GeoIP.dat.gz" % MM_DATA_PATH)
urllib.urlretrieve ("http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz",
"%s/GeoLiteCity.dat.gz" % MM_DATA_PATH)
urllib.urlretrieve ("http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz",
"%s/GeoIPASNum.dat.gz" % MM_DATA_PATH)
urllib.urlretrieve ("http://geolite.maxmind.com/download/geoip/database/GeoLiteCityv6-beta/GeoLiteCityv6.dat.gz",
"%s/GeoLiteCityv6.dat.gz" % MM_DATA_PATH)
os.system("gunzip %s/GeoIP.dat.gz" % MM_DATA_PATH)
os.system("gunzip %s/GeoLiteCity.dat.gz" % MM_DATA_PATH)
os.system("gunzip %s/GeoIPASNum.dat.gz" % MM_DATA_PATH)
os.system("gunzip %s/GeoLiteCityv6.dat.gz" % MM_DATA_PATH)
