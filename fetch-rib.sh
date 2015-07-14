#!/bin/bash

export PATH=$PATH:~ixmaps/bin

# retrieve the RouteViews BGP data as of 0h00 UTC today and generate the origin-AS file
# http://archive.routeviews.org/bgpdata/2010.06/RIBS/rib.20100603.0000.bz2
IXMAPS_DATA=$HOME/ix-data

quiet_flag=
if [ "$1" == "-q" ] ; then
	quiet_flag=-q
	shift
fi

cd $IXMAPS_DATA || {
	echo "$0: can't find ixmaps data directory."
	exit 1
}

today_yyyy=`date +%Y`
today_mm=`date +%m`
today_dd=`date +%d`

today="${today_yyyy}${today_mm}${today_dd}"
bz2_filename="rib.${today}.0000.bz2"
bin_filename="rib.${today}.0000"
oas_filename="rib.${today}.0000.oas"
url="http://archive.routeviews.org/bgpdata/${today_yyyy}.${today_mm}/RIBS/${bz2_filename}"

echo "retrieving $url"
wget $quiet_flag $url || {
	echo "$0: can't retrieve current RouteViews RIB data $bz2_filename"
	exit 1
}

echo "decompressing BGP dump"
bunzip2 -k $bz2_filename || {
	echo "$0: failed to decompress $bz2_filename"
	exit 1
}

echo "extracting origin-AS information"
bgpdump -m $bin_filename | mrt_split.py > ${oas_filename}.tmp || {
	echo "$0: failed to extract origin-AS information"
	exit 1
}

echo "cleaning up"
mv ${oas_filename}.tmp ${oas_filename}
ln -sf ${oas_filename} rib.current.oas

# don't litter with 600MB files
rm $bin_filename

