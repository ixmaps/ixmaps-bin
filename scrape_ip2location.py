#!/usr/bin/python

# This script scrapes ip2location for geolocation values, then populates them to our iplocation_ip_addrs table

import json
import re
import psycopg2
import psycopg2.extras

def main():
  with open('/Users/colin/dev/ixmaps/ixmaps-bin/config.json') as f:
    config = json.load(f)

  try:
    conn = psycopg2.connect("dbname='"+config['dbname']+"' user='"+config['dbuser']+"' host='localhost' password='"+config['dbpassword']+"'")
  except:
    print "I am unable to connect to the database"
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  scrape(conn, cur)

  conn.close()


def scrape(conn, cur):
  access_token = 'K973M6RdNCHz8mv'

  # START HERE? OR DITCH THIS ENTIRELY

  curl "https://api.ip2location.com/v2/?ip=2607:f2c0:e360:1201:a835:12e1:8b52:5799&key={access_token}&package=WS24&addon=continent,country,region,city,geotargeting,country_groupings,time_zone_info"

  cur.execute("""SELECT ip_addr FROM ip_addr_info WHERE ip_addr not in (SELECT ip_addr FROM ipinfo_ip_addr) AND text(ip_addr) NOT LIKE '10.%' LIMIT 10000""")
  # cur.execute("""SELECT ip_addr FROM ip_addr_info WHERE ip_addr not in (SELECT ip_addr FROM ipinfo_ip_addr) AND (mm_country = '%s' OR mm_country = '%s') LIMIT 10000""" % ("CA", "US"))
  rows = cur.fetchall()
  for row in rows:
    ip = row['ip_addr']
    print "Scraping: ", ip

    details = handler.getDetails(ip)

    if details and hasattr(details, 'loc') and hasattr(details, 'latitude') and hasattr(details, 'longitude'):
      print "\nRetrived: "+details.ip
      print "\nLoc: "+details.loc
      print "\nLat: "+details.latitude
      print "\nLong: "+details.longitude
      print details.all

      insert_val(details, conn, cur)


def insert_val(details, conn, cur):
  print "\nInserting...\n"
  query = """INSERT INTO ipinfo_ip_addr (ip_addr, city, region, country, postal, lat, long, hostname) values (%s, %s, %s, %s, %s, %s, %s, %s);"""
  data = (details.ip, getattr(details, 'city', ''), getattr(details, 'region', ''), getattr(details, 'country', ''), getattr(details, 'postal', '')[:11], details.latitude, details.longitude, getattr(details, 'hostname', ''),)
  cur.execute(query, data)
  conn.commit()


main()