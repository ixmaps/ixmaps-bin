#!/usr/bin/python

import json
import re
import psycopg2
import psycopg2.extras
import socket, struct

def main():
    with open('/Users/colin/dev/ixmaps/ixmaps-bin/config.json') as f:
        config = json.load(f)

    try:
        conn = psycopg2.connect("dbname='"+config['dbname']+"' user='"+config['dbuser']+"' host='localhost' password='"+config['dbpassword']+"'")
    except:
        print "I am unable to connect to the database"
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sys.exit("This shit is broken!")

    update_asnum_asname(conn, cur)

    cur.close()
    conn.close()

def update_asnum_asname(conn, cur):
    skip_count = 0

    cur.execute("""SELECT * FROM ip2_location WHERE asnum IS NULL ORDER BY ip_addr""")
    rows = cur.fetchall()
    for ip_row in rows:
        ip_int = struct.unpack("!L", socket.inet_aton(ip_row['ip_addr']))[0]
        print "Verifying: ", ip_int

        cur.execute("""SELECT * FROM ip2location_asn WHERE ip_from >= %s and ip_to <= %s""" % (ip_int, ip_int))
        if cur.rowcount != 1:
            print "More than one row found - skipping..."
            skip_count += 1
            continue

        asn_row = cur.fetchone()
        print asn_row

        if asn_row['asn'] != "-":
            update_row(asn_row['asn'], ip_row['ip_addr'], conn, cur)
        else:
            print "Invalid asn"


        print "Skipped: ", str(skip_count)


def update_row(asnum, ip_addr, conn, cur):
    query = """UPDATE gl_analysis SET i2_asn=%s WHERE ip_addr=%s;"""
    data = (asnum, ip_addr,)
    cur.execute(query, data)
    conn.commit()


main()