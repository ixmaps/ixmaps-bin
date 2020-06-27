#!/usr/bin/python

import psycopg2
import psycopg2.extras
import requests
from requests.exceptions import ConnectionError

# START HERE - is cbc.ca still unreachable on the server? If no, revert all these changes...
# If we're still getting a lot of false negatives, what about ping instead of request?


def main():
  try:
    conn = psycopg2.connect("dbname='ixmaps' user='ixmaps' host='localhost' password=''")
  except:
    print "I am unable to connect to the database"
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  verify(conn, cur)

  conn.close()

  # www.calma.qc.ca should fail
  # homedepot.com should succeed
  # cbc.ca should succeed
  # 23.239.6.109 fails with both
  # 65.19.143.9 fails with request, succeeds with ping


  # url = 'cbc.ca'
  # url = url.replace("http://", '')
  # url = url.replace("https://", '')
  # url = "http://" + url
  # try:
  #   request = requests.get(url, timeout=10)
  # except requests.exceptions.RequestException as e:
  #   print('Unreachable!')
  # else:
  #   print(url+' is reachable...')

  # if ping('cbc.ca'):
  #   print("Ping says this is reachable")
  # else:
  #   print("Ping says unreachable!")


def verify(conn, cur):
  cur.execute("""SELECT url FROM trset_target""")
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
      print(url+' is reachable...')
      update_reachable(row['url'], 'true', conn, cur)
    except requests.exceptions.RequestException as e:
      print('Unreachable')
      update_reachable(row['url'], 'false', conn, cur)

import platform    # For getting the operating system name
import subprocess  # For executing a shell command

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0

def update_reachable(url, flag, conn, cur):
  query = """UPDATE trset_target SET reachable=%s WHERE url=%s;"""
  data = (flag, url,)
  cur.execute(query, data)
  conn.commit()

main()