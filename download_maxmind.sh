#!/bin/bash

# This script downloads the new version of maxmind data. It is triggered by a cronjob on the 15th of each month
# NB: remember to add the license key and user values to /etc/environment

MM_DATA_PATH="/home/ixmaps/ix-data/mm-data"

echo "Downloading new version of MaxMind data on "$(date +%F)

mkdir $MM_DATA_PATH/tmp
mv $MM_DATA_PATH/GeoLite2-ASN.mmdb $MM_DATA_PATH/tmp/
mv $MM_DATA_PATH/GeoLite2-City.mmdb $MM_DATA_PATH/tmp/

asn_zip=$(wget -O $MM_DATA_PATH/GeoLite2-ASN.tar.gz --user=$MM_USER --password=$MM_LICENSE_KEY 'https://download.maxmind.com/geoip/databases/GeoLite2-ASN/download?suffix=tar.gz')
asn_download_status=$?
city_zip=$(wget -O $MM_DATA_PATH/GeoLite2-City.tar.gz --user=$MM_USER --password=$MM_LICENSE_KEY 'https://download.maxmind.com/geoip/databases/GeoLite2-City/download?suffix=tar.gz')
city_download_status=$?

if [ $asn_download_status -ne 0 ] || [ $city_download_status -ne 0 ]; then
  echo "Something went wrong with the download, reverting to previous data..."
  mv $MM_DATA_PATH/tmp/GeoLite2-ASN.mmdb $MM_DATA_PATH/
  mv $MM_DATA_PATH/tmp/GeoLite2-City.mmdb $MM_DATA_PATH/
  rm -rf $MM_DATA_PATH/tmp
  exit 1
fi

rm -rf $MM_DATA_PATH/tmp

tar -xvzf $MM_DATA_PATH/GeoLite2-ASN.tar.gz --strip-components=1 -C $MM_DATA_PATH
tar -xvzf $MM_DATA_PATH/GeoLite2-City.tar.gz --strip-components=1 -C $MM_DATA_PATH
