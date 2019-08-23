#!/bin/bash

# This script downloads the new version of maxmind data. It is triggered by a cronjob on the 15th of each month

MM_DATA_PATH="/home/ixmaps/ix-data/mm-data"

rm $MM_DATA_PATH/*

wget -P $MM_DATA_PATH https://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz
wget -P $MM_DATA_PATH https://geolite.maxmind.com/download/geoip/database/GeoLite2-ASN.tar.gz

tar -xvzf $MM_DATA_PATH/GeoLite2-City.tar.gz --strip-components=1 -C $MM_DATA_PATH
tar -xvzf $MM_DATA_PATH/GeoLite2-ASN.tar.gz --strip-components=1 -C $MM_DATA_PATH