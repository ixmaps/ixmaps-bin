#!/usr/bin/python

# This script confirms whether the trset URLs are all valid. It is triggered by a cronjob every night.
# NB: remember to update the password as required on the server

import psycopg2
import psycopg2.extras
# import requests
# from requests.exceptions import ConnectionError
import subprocess


def main():
  try:
    conn = psycopg2.connect("dbname='ixmaps' user='ixmaps' host='localhost' password=''")
  except:
    print "I am unable to connect to the database"
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  verify(conn, cur)

  conn.close()


def ping(host):
  """
  Returns True if host (str) responds to a ping request.
  Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
  """

  # Building the command
  command = ['ping', '-c', '1', host]

  return subprocess.call(command) == 0


def verify(conn, cur):
  cur.execute("""SELECT url FROM trset_target""")
  rows = cur.fetchall()
  for row in rows:
    url = row['url']
    print "Verifying: ", url

    if ping(url):
      print("Reachable")
      update_reachable(url, 'true', conn, cur)
    else:
      print(url+" is unreachable...")
      update_reachable(url, 'false', conn, cur)

    # request requires very specific formatting (http://xyz.abc)
    # url = url.replace("http://", '')
    # url = url.replace("https://", '')
    # url = "http://" + url
    # try:
    #   request = requests.get(url, timeout=10)
    #   print('Reachable')
    #   update_reachable(row['url'], 'true', conn, cur)
    # except requests.exceptions.RequestException as e:
    #   print(url+' is unreachable...')
    #   update_reachable(row['url'], 'false', conn, cur)


def update_reachable(url, flag, conn, cur):
  query = """UPDATE trset_target SET reachable=%s WHERE url=%s;"""
  data = (flag, url,)
  cur.execute(query, data)
  conn.commit()


main()