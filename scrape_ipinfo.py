#!/usr/bin/python

# This script scrapes ipinfo.io for geolocation values, then populates them to our ipinfo_ip_addrs table

import json
import re
import psycopg2
import psycopg2.extras
import ipinfo

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
  access_token = '43ad6873665f77'
  handler = ipinfo.getHandler(access_token)

  cur.execute("""SELECT ip_addr FROM ip_addr_info WHERE ip_addr not in (SELECT ip_addr FROM ipinfo_ip_addrs) AND gl_override IS NOT NULL LIMIT 18786""")
  rows = cur.fetchall()
  for row in rows:
    ip = row['ip_addr']
    print "Scraping: ", ip

    details = handler.getDetails(ip)

    if details:
      print "\nRetrived: "+details.ip
      print "\nCity: "+details.city
      print "\nCountry: "+details.country
      print "\nLoc: "+details.loc
      print "\nLat: "+details.latitude
      print "\nLong: "+details.longitude
      print details.all

      insert_val(details, conn, cur)


def insert_val(details, conn, cur):
  print "\nInserting...\n"
  query = """INSERT INTO ipinfo_ip_addrs (ip_addr, city, region, country, postal, lat, long, hostname) values (%s, %s, %s, %s, %s, %s, %s, %s);"""
  data = (details.ip, details.city, getattr(details, 'region', ''), details.country, getattr(details, 'postal', ''), details.latitude, details.longitude, getattr(details, 'hostname', ''),)
  cur.execute(query, data)
  conn.commit()


main()