#!/bin/bash

# This script generates a small text file that is used by the website (db-stats.js for index.php)

contributorsCount=$(psql ixmaps -t -c "SELECT COUNT (DISTINCT submitter) FROM traceroute")
destinationsCount=$(psql ixmaps -t -c "SELECT COUNT (DISTINCT dest) FROM traceroute")
traceroutesCount=$(psql ixmaps -t -c "SELECT COUNT (DISTINCT id) FROM traceroute")
latestTraceroute=$(psql ixmaps -t -c "SELECT to_char(sub_time, 'DD Mon YYYY') FROM traceroute ORDER BY id DESC LIMIT 1;")

json="var dbStats = {
  'total_submitters': "$contributorsCount",
  'total_destinations': "$destinationsCount",
  'total_traceroutes': "$traceroutesCount",
  'latest_contribution': '"$latestTraceroute"'
}"

echo $json > /srv/www/website/_includes/db-stats.json