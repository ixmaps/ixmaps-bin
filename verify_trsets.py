#!/usr/bin/python

# This script confirms whether the trset URLs are all valid. It is triggered by a cronjob every night.
# NB: remember to update the password as required on the server

# We check urls that are only digits (eg an ip addr as the hostname) with a ping,
# other urls with a GET (since non-terminating routes are still of value to us)

import json
import re
import psycopg2
import psycopg2.extras
import requests
from requests.exceptions import ConnectionError
import subprocess

def main():
    with open('/home/ixmaps/bin/config.json') as f:
      config = json.load(f)

    try:
      conn = psycopg2.connect("dbname='"+config['dbname']+"' user='"+config['dbuser']+"' host='localhost' password='"+config['dbpassword']+"'")
    except:
        print "I am unable to connect to the database"
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    verify(conn, cur)

    conn.close()


def ping(host):
    command = ['ping', '-c', '1', host]
    return subprocess.call(command) == 0


def verify(conn, cur):
    cur.execute("""SELECT url FROM trset_target ORDER BY id""")
    rows = cur.fetchall()
    for row in rows:
        url = row['url']
        print "Verifying: ", url

        if bool(re.match('[\d/.]+$', url)):
            print "PING"
            if ping(url):
                print "Reachable\n\n"
                update_reachable(url, 'true', conn, cur)
            else:
                print(url+" is unreachable...\n\n")
                update_reachable(url, 'false', conn, cur)
        else:
            print "GET"
            # request requires very specific formatting (http://xyz.abc)
            url = url.replace("http://", '')
            url = url.replace("https://", '')
            url = "http://" + url
            try:
                request = requests.get(url, timeout=10)
                print('Reachable\n\n')
                update_reachable(row['url'], 'true', conn, cur)
            except requests.exceptions.RequestException as e:
                print(url+' is unreachable...\n\n')
                update_reachable(row['url'], 'false', conn, cur)


def update_reachable(url, flag, conn, cur):
    query = """UPDATE trset_target SET reachable=%s WHERE url=%s;"""
    data = (flag, url,)
    cur.execute(query, data)
    conn.commit()


main()