#!/usr/bin/env python3

import psycopg2
import psycopg2.extras
import requests
from requests.exceptions import ConnectionError

def main():
  try:
    conn = psycopg2.connect("dbname='ixmaps' user='ixmaps' host='localhost'")
  except:
    print "I am unable to connect to the database"
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  verify(conn, cur)

  conn.close()

def verify(conn, cur):
  cur.execute("""SELECT url FROM trset_targets""")
  rows = cur.fetchall()
  for row in rows:
    url = row['url']
    print "Verifying:", url

    # cleanup, as request requires very specific formatting (http://xyz.abc)
    url = url.replace("http://", '')
    url = url.replace("https://", '')
    url = "http://" + url
    try:
      request = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
      print('Unreachable')
      query = """UPDATE trset_targets SET reachable = false WHERE url=%s;"""
      data = (row['url'],)
      cur.execute(query, data)
      conn.commit()
    else:
      print(url+' is reachable...')


main()