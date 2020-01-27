#!/bin/bash

# This script downloads the new version of maxmind data. It is triggered by a cronjob on the 15th of each month
# NB: this uses an env variable for MM_LICENSE_KEY

MM_DATA_PATH="/home/ixmaps/ix-data/mm-data"

rm $MM_DATA_PATH/*

wget -O $MM_DATA_PATH/GeoLite2-ASN.tar.gz "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=${MM_LICENSE_KEY}&suffix=tar.gz"
wget -O $MM_DATA_PATH/GeoLite2-City.tar.gz "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${MM_LICENSE_KEY}&suffix=tar.gz"

tar -xvzf $MM_DATA_PATH/GeoLite2-ASN.tar.gz --strip-components=1 -C $MM_DATA_PATH
tar -xvzf $MM_DATA_PATH/GeoLite2-City.tar.gz --strip-components=1 -C $MM_DATA_PATH