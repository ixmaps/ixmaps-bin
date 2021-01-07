#!/bin/bash

# This script downloads the new version of ip2Location data. It is triggered by a cronjob on the 15th of each month
# NB: remember to add the login and password below, and update the data path
# NB: this relies on a custom perl script from https://www.ip2location.com/free/downloader

IP2_DATA_PATH="/home/ixmaps/bin"

echo "Downloading new version of IP2Location data on "$(date +%F)

# download the pieces we need
perl download-ip2location.pl -package DB9LITE -login $IP2_EMAIL -password $IP2_PASSWORD
unzip $IP2_DATA_PATH/IP2LOCATION-LITE-DB9.CSV.ZIP
rm $IP2_DATA_PATH/LICENSE_LITE.TXT
rm $IP2_DATA_PATH/README_LITE.TXT
perl download-ip2location.pl -package DBASNLITE -login $IP2_EMAIL -password $IP2_PASSWORD
unzip $IP2_DATA_PATH/IP2LOCATION-LITE-ASN.ZIP
rm $IP2_DATA_PATH/LICENSE_LITE.TXT
rm $IP2_DATA_PATH/README_LITE.TXT

# error checking
if [[ ! -f "$IP2_DATA_PATH/IP2LOCATION-LITE-DB9.CSV" || ! -f "$IP2_DATA_PATH/IP2LOCATION-LITE-ASN.CSV" ]]; then
  echo "Something went wrong with the download, exiting..."
  exit 1
fi

# create and populate the ip addr table
psql ixmaps -c "CREATE TABLE ip2location_ip_addr_temp(
  ip_from bigint NOT NULL,
  ip_to bigint NOT NULL,
  country_code character(2) NOT NULL,
  country_name character varying(64) NOT NULL,
  region_name character varying(128) NOT NULL,
  city_name character varying(128) NOT NULL,
  latitude real NOT NULL,
  longitude real NOT NULL,
  zip_code character varying(30) NOT NULL,
  CONSTRAINT ip2location_db9_pkey PRIMARY KEY (ip_from, ip_to)
);"
psql ixmaps -c "COPY ip2location_ip_addr_temp FROM '$IP2_DATA_PATH/IP2LOCATION-LITE-DB9.CSV' WITH CSV QUOTE AS '\"';"

# create and populate the asn table
psql ixmaps -c "CREATE TABLE ip2location_asn_temp(
  ip_from bigint NOT NULL,
  ip_to bigint NOT NULL,
  cidr character varying(18) NOT NULL,
  asn character varying(10) NOT NULL,
  \"as\" character varying(256) NOT NULL,
  CONSTRAINT ip2location_asn_temp_pkey PRIMARY KEY (ip_from, ip_to)
);"
psql ixmaps -c "SET CLIENT_ENCODING TO 'latin1';"
psql ixmaps -c "COPY ip2location_asn_temp FROM '$IP2_DATA_PATH/IP2LOCATION-LITE-ASN.CSV' WITH CSV QUOTE AS '\"';"

# join the temp tables into the final table
psql ixmaps -c "DROP table ip2location_ip_addr_testing"
psql ixmaps -c "SELECT i.* ,a.asn, a.as into ip2location_ip_addr_testing from ip2location_ip_addr_temp i join ip2location_asn_temp a on i.ip_from = a.ip_from;"
# table cleanup
psql ixmaps -c "ALTER table ip2location_ip_addr_testing RENAME COLUMN country_code TO country;"
psql ixmaps -c "ALTER table ip2location_ip_addr_testing RENAME COLUMN asn TO asnum;"
psql ixmaps -c "ALTER table ip2location_ip_addr_testing RENAME COLUMN \"as\" TO asname;"
psql ixmaps -c "DROP table ip2location_ip_addr_temp;"
psql ixmaps -c "DROP table ip2location_asn_temp;"

# dir cleanup
rm $IP2_DATA_PATH/IP2LOCATION-LITE-DB9.CSV.ZIP
rm $IP2_DATA_PATH/IP2LOCATION-LITE-DB9.CSV
rm $IP2_DATA_PATH/IP2LOCATION-LITE-ASN.ZIP
rm $IP2_DATA_PATH/IP2LOCATION-LITE-ASN.CSV