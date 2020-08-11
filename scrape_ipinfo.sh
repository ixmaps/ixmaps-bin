#!/bin/bash

# This script scrapes ipinfo.io for geolocation values, then populates them to our ipinfo_ip_addrs table

TOKEN=43ad6873665f77

echo "Scraping..."

ip_addrs=$(psql ixmaps -t -c "select ip_addr from ip_addr_info where ip_addr not in (select ip_addr from ipinfo_ip_addrs) limit 1;")

for ip in $ip_addrs; do
  echo "Curling: "$ip
  target="ipinfo.io/"$ip"/geo?token="$TOKEN
  response_json="$(curl -s $target)"

  echo $response_json
  # break if 429
  # if `echo ${response_json} | jq -r '.error'` is not null

  ip=`echo ${response_json} | jq -r '.ip'`
  city=`echo ${response_json} | jq -r '.city'`
  region=`echo ${response_json} | jq -r '.region'`
  country=`echo ${response_json} | jq -r '.country'`
  postal=`echo ${response_json} | jq -r '.postal'`
  loc=`echo ${response_json} | jq -r '.loc'`
  lat=`echo ${loc} | cut -d',' -f1`
  long=`echo ${loc} | cut -d',' -f2`

  echo $ip
  echo $city
  echo $region
  echo $country
  echo $postal
  echo $lat
  echo $long

done

