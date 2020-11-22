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
        print("I am unable to connect to the database")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    scrape(conn, cur)

    conn.close()


def scrape(conn, cur):
    # access_token = '43ad6873665f77'
    access_token = '61a406bb0bae69'
    handler = ipinfo.getHandler(access_token)

    # add a new column for created_at and updated_at
    # add back the 192 and 172 filters
    # date the tables?

    cur.execute("""SELECT ip_addr FROM ip_addr_info WHERE ip_addr not in (SELECT ip_addr FROM ipinfo_ip_addr_paid) ORDER BY random() limit 50000;""")
    # cur.execute("""SELECT ip_addr FROM ip_addr_info WHERE ip_addr not in (SELECT ip_addr FROM ipinfo_ip_addr) AND text(ip_addr) NOT LIKE '10.%' AND text(ip_addr) NOT LIKE '100.%' AND text(ip_addr) NOT LIKE '172.%' AND text(ip_addr) NOT LIKE '192.1%' LIMIT 10000""")
    # cur.execute("""SELECT ip_addr FROM ip_addr_info WHERE ip_addr not in (SELECT ip_addr FROM ipinfo_ip_addr) AND (mm_country = '%s' OR mm_country = '%s') LIMIT 10000""" % ("CA", "US"))
    rows = cur.fetchall()
    for row in rows:
        ip = row['ip_addr']
        print("Scraping: ", ip)

        details = handler.getDetails(ip)

        if details and hasattr(details, 'loc') and hasattr(details, 'latitude') and hasattr(details, 'longitude'):
            print("\nRetrieved: "+details.ip)
            print("\nLat: "+details.latitude)
            print("\nLong: "+details.longitude)
            print(details.all)

            insert_val(details, conn, cur)


def insert_val(details, conn, cur):
    print("\nInserting...\n")
    asnum = get_asn_values(details)[0]
    asname = get_asn_values(details)[1]
    query = """INSERT INTO ipinfo_ip_addr_paid (ip_addr, asnum, asname, city, region, country, postal, lat, long, hostname) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    data = (details.ip, asnum, asname, getattr(details, 'city', ''), getattr(details, 'region', ''), getattr(details, 'country', ''), getattr(details, 'postal', '')[:11], details.latitude, details.longitude, getattr(details, 'hostname', ''),)
    cur.execute(query, data)
    conn.commit()


def get_asn_values(details):
    if hasattr(details, 'org'):
        asn_details = details.org.split(' ', 1)
        asnum = asn_details[0][2:len(asn_details[0])]
        asname = asn_details[1]
        print("\nASNum: "+asnum)
        print("\nASName: "+asname)
        return [asnum, asname]

    return [None, '']

main()