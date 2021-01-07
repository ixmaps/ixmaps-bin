#!/usr/bin/perl -w
###############################################################################
# IP2Location Download Client
###############################################################################
# Perl script to download IP2Location(tm) database from the server.
#
# Note: User subscription login and password required.
#
# There is no warranty or guarantee conveyed by the author/copyright holder of
# this script. By obtaining, installing, and using this program, you agree and
# understand that the author and copyright holder are not responsible for any
# damages caused under any conditions due to the malfunction of the script(s)
# on your server or otherwise.
#
# REVISION HISTORY
# ================
# 1.0.0   Initial Release
# 1.1.0   Support IP2Location DB11 + DB12 + DB13 + DB14
# 1.2.0   Change URL to IP2Location.com
# 2.0.0   Support IP2Location DB15 + DB16 + DB17 + DB18
#         Support IP2Proxy PX1
#         Support Command Prompt in Windows as EXE
# 2.1.0   Support Proxy Server
# 2.2.0   Support CIDR + ACL
# 3.0.0   Support IP2Location DB19 + DB20
# 3.1.0   Support New Web Site Structure
# 4.0.0   Support DB21 + DB22 + DB23 + DB24
#         Support Download via SSL
#         Support LITE DBs.
# 5.0.0   Support DB1-DB24 IPV6
#         Support LITE IPV6
#         Update New Download URL
# 6.0.0   Support IP2Proxy PX2-PX4
#         Support -showall switch
# 7.0.0   Support IP2Proxy PX1BIN-PX4BIN
#         Support LITE ASN
# 8.0.0   Support IP2Proxy LITE PX1LITE-PX4LITE
#         Support IP2Proxy LITE PX1BINLITE-PX4BINLITE
# 8.1.0   Support POST instead of GET Protocol
#         Support file size validation
# 8.2.0   Support TOKEN as credential for download access
# 8.3.0   Support CIDR + ACL IPV6
# 8.4.0   Force SSL / HTTPS Download
# 9.0.0   Support IP2Proxy PX5-PX8
#         Support IP2Proxy LITE PX5-PX8
# 9.1.0   Support IP2Proxy IPV6
#         Support IP2Proxy LITE IPV6
# 9.2.0   Support IP2Proxy PX9-PX10
#         Support IP2Proxy LITE PX9-PX10
#
# Copyright (C) 2002-2020 IP2Location.com. All rights reserved.
#
###############################################################################
use strict;
use Getopt::Long;

$|++;
my $VERSION = "9.2.0";
eval("use LWP;"); die "[ERROR] LWP library required. ($VERSION)\n" if $@;
eval("use LWP::Protocol::https;"); die "[ERROR] Please install Perl LWP::Protocol::https library to support HTTPS download.  ($VERSION)\n" if $@;
use LWP;
use LWP::Protocol::https;

my $opt_package = "";
my $opt_login = "";
my $opt_password = "";
my $opt_output = "";
my $opt_proxy = "";
my $opt_token = "";
my $help = 0;
my $ssl = 1;
my $nossl = 0;
my $showall = 0;

my $result = GetOptions('package=s' => \$opt_package,
	'login:s' => \$opt_login,
	'password:s' => \$opt_password,
	'output:s' => \$opt_output,
	'proxy:s' => \$opt_proxy,
	'token:s' => \$opt_token,
	'help' => \$help,
	'showall' => \$showall,
	'nossl' => \$nossl,
	'ssl' => \$ssl);

if ($help) {
	&print_help;
	exit(0);
}

if ($showall) {
	&print_showall;
	exit(0);
}

if ($nossl) {
	$ssl = 0;
}

my $final_data = "";
my $total_size = 0;
my $expiry_date = "";
my $database_version = "";
my $https = ($ssl) ? 's' : '';

my $urlversion = "http" . $https . "://www.ip2location.com/downloads/downloaderversion.txt";
my $urlinfo = "http" . $https . "://www.ip2location.com/download-info";
my $url = "http" . $https . "://www.ip2location.com/download";

my $login = '';
my $password = '';
my $filename = '';
my $output = '';
my $token = '';
my $package = '';
my $proxy = '';

if ($opt_package ne "") {
	$package = $opt_package;
} else {
	&print_help;
	print STDERR "\n[Error] Missing -package command line switch or parameter.\n\n";
	exit(0);
}

if ($opt_token ne "") {
	$token = $opt_token;
} else {
	if ($opt_login ne "") {
		$login = $opt_login;
	} else {
		&print_help;
		print STDERR "\n[Error] Missing -token command line switch or parameter.\n\n";
		exit(0);
	}

	if ($opt_password ne "") {
		$password = $opt_password;
	} else {
		&print_help;
		print STDERR "\n[Error] Missing -password command line switch or parameter.\n\n";
		exit(0);
	}
}

if ($opt_proxy ne "") {
	$proxy = lc($opt_proxy);
}

$package = uc($package);

if ($package eq "DB1") { $filename = "IPCountry-FULL.zip"; $output = "IP-COUNTRY-FULL.ZIP"; }
elsif ($package eq "DB2") { $filename = "IPISP-FULL.zip"; $output = "IP-COUNTRY-ISP-FULL.ZIP"; }
elsif ($package eq "DB3") { $filename = "IP-COUNTRY-REGION-CITY-FULL.ZIP";  $output = $filename; }
elsif ($package eq "DB4") { $filename = "IP-COUNTRY-REGION-CITY-ISP-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB5") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB6") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB7") { $filename = "IP-COUNTRY-REGION-CITY-ISP-DOMAIN-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB8") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB9") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB10") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-ISP-DOMAIN-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB11") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB12") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB13") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-TIMEZONE-NETSPEED-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB14") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB15") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-AREACODE-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB16") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB17") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-TIMEZONE-NETSPEED-WEATHER-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB18") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB19") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN-MOBILE-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB20") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB21") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-AREACODE-ELEVATION-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB22") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-ELEVATION-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB23") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN-MOBILE-USAGETYPE-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB24") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-ELEVATION-USAGETYPE-FULL.ZIP"; $output = $filename; }
elsif ($package eq "DB1BIN") { $filename = "IP-COUNTRY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB2BIN") { $filename = "IP-COUNTRY-ISP.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB3BIN") { $filename = "IP-COUNTRY-REGION-CITY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB4BIN") { $filename = "IP-COUNTRY-REGION-CITY-ISP.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB5BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB6BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB7BIN") { $filename = "IP-COUNTRY-REGION-CITY-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB8BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB9BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB10BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB11BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB12BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB13BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-TIMEZONE-NETSPEED.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB14BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB15BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-AREACODE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB16BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB17BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-TIMEZONE-NETSPEED-WEATHER.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB18BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB19BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN-MOBILE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB20BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB21BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-AREACODE-ELEVATION.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB22BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-ELEVATION.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB23BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN-MOBILE-USAGETYPE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB24BIN") { $filename = "IP-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-ELEVATION-USAGETYPE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB1CIDR") { $filename = "IP2LOCATION-IP-COUNTRY-CIDR.ZIP"; $output = $filename; }
elsif ($package eq "DB1ACL") { $filename = "IP2LOCATION-IP-COUNTRY-ACL.ZIP"; $output = $filename; }
elsif ($package eq "DB1LITE") { $filename = "IP2LOCATION-LITE-DB1.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB3LITE") { $filename = "IP2LOCATION-LITE-DB3.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB5LITE") { $filename = "IP2LOCATION-LITE-DB5.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB9LITE") { $filename = "IP2LOCATION-LITE-DB9.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB11LITE") { $filename = "IP2LOCATION-LITE-DB11.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB1LITEBIN") { $filename = "IP2LOCATION-LITE-DB1.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB3LITEBIN") { $filename = "IP2LOCATION-LITE-DB3.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB5LITEBIN") { $filename = "IP2LOCATION-LITE-DB5.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB9LITEBIN") { $filename = "IP2LOCATION-LITE-DB9.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB11LITEBIN") { $filename = "IP2LOCATION-LITE-DB11.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB1IPV6") { $filename = "IPV6-COUNTRY.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB2IPV6") { $filename = "IPV6-COUNTRY-ISP.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB3IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB4IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-ISP.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB5IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB6IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB7IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-ISP-DOMAIN.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB8IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB9IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB10IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-ISP-DOMAIN.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB11IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB12IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB13IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-TIMEZONE-NETSPEED.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB14IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB15IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-AREACODE.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB16IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB17IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-TIMEZONE-NETSPEED-WEATHER.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB18IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB19IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN-MOBILE.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB20IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB21IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-AREACODE-ELEVATION.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB22IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-ELEVATION.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB23IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN-MOBILE-USAGETYPE.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB24IPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-ELEVATION-USAGETYPE.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB1BINIPV6") { $filename = "IPV6-COUNTRY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB2BINIPV6") { $filename = "IPV6-COUNTRY-ISP.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB3BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB4BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-ISP.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB5BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB6BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB7BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB8BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB9BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB10BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB11BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB12BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB13BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-TIMEZONE-NETSPEED.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB14BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB15BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-AREACODE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB16BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB17BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-TIMEZONE-NETSPEED-WEATHER.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB18BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB19BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN-MOBILE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB20BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB21BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-AREACODE-ELEVATION.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB22BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-ELEVATION.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB23BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ISP-DOMAIN-MOBILE-USAGETYPE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB24BINIPV6") { $filename = "IPV6-COUNTRY-REGION-CITY-LATITUDE-LONGITUDE-ZIPCODE-TIMEZONE-ISP-DOMAIN-NETSPEED-AREACODE-WEATHER-MOBILE-ELEVATION-USAGETYPE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB1CIDRIPV6") { $filename = "IP2LOCATION-IPV6-COUNTRY-CIDR.ZIP"; $output = $filename; }
elsif ($package eq "DB1ACLIPV6") { $filename = "IP2LOCATION-IPB6-COUNTRY-ACL.ZIP"; $output = $filename; }
elsif ($package eq "DB1LITEIPV6") { $filename = "IP2LOCATION-LITE-DB1-IPV6.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB3LITEIPV6") { $filename = "IP2LOCATION-LITE-DB3-IPV6.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB5LITEIPV6") { $filename = "IP2LOCATION-LITE-DB5-IPV6.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB9LITEIPV6") { $filename = "IP2LOCATION-LITE-DB9-IPV6.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB11LITEIPV6") { $filename = "IP2LOCATION-LITE-DB11-IPV6.CSV.ZIP"; $output = $filename; }
elsif ($package eq "DB1LITEBINIPV6") { $filename = "IP2LOCATION-LITE-DB1-IPV6.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB3LITEBINIPV6") { $filename = "IP2LOCATION-LITE-DB3-IPV6.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB5LITEBINIPV6") { $filename = "IP2LOCATION-LITE-DB5-IPV6.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB9LITEBINIPV6") { $filename = "IP2LOCATION-LITE-DB9-IPV6.BIN.ZIP"; $output = $filename; }
elsif ($package eq "DB11LITEBINIPV6") { $filename = "IP2LOCATION-LITE-DB11-IPV6.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX1") { $filename = "PX1-IP-COUNTRY.ZIP"; $output = $filename; }
elsif ($package eq "PX2") { $filename = "PX2-IP-PROXYTYPE-COUNTRY.ZIP"; $output = $filename; }
elsif ($package eq "PX3") { $filename = "PX3-IP-PROXYTYPE-COUNTRY-REGION-CITY.ZIP"; $output = $filename; }
elsif ($package eq "PX4") { $filename = "PX4-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP.ZIP"; $output = $filename; }
elsif ($package eq "PX5") { $filename = "PX5-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN.ZIP"; $output = $filename; }
elsif ($package eq "PX6") { $filename = "PX6-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE.ZIP"; $output = $filename; }
elsif ($package eq "PX7") { $filename = "PX7-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN.ZIP"; $output = $filename; }
elsif ($package eq "PX8") { $filename = "PX8-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN.ZIP"; $output = $filename; }
elsif ($package eq "PX9") { $filename = "PX9-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT.ZIP"; $output = $filename; }
elsif ($package eq "PX10") { $filename = "PX10-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT-RESIDENTIAL.ZIP"; $output = $filename; }
elsif ($package eq "PX1BIN") { $filename = "PX1-IP-COUNTRY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX2BIN") { $filename = "PX2-IP-PROXYTYPE-COUNTRY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX3BIN") { $filename = "PX3-IP-PROXYTYPE-COUNTRY-REGION-CITY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX4BIN") { $filename = "PX4-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX5BIN") { $filename = "PX5-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX6BIN") { $filename = "PX6-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX7BIN") { $filename = "PX7-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX8BIN") { $filename = "PX8-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX9BIN") { $filename = "PX9-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX10BIN") { $filename = "PX10-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT-RESIDENTIAL.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX1LITE") { $filename = "PX1-LITE-IP-COUNTRY.ZIP"; $output = $filename; }
elsif ($package eq "PX2LITE") { $filename = "PX2-LITE-IP-PROXYTYPE-COUNTRY.ZIP"; $output = $filename; }
elsif ($package eq "PX3LITE") { $filename = "PX3-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY.ZIP"; $output = $filename; }
elsif ($package eq "PX4LITE") { $filename = "PX4-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP.ZIP"; $output = $filename; }
elsif ($package eq "PX5LITE") { $filename = "PX5-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN.ZIP"; $output = $filename; }
elsif ($package eq "PX6LITE") { $filename = "PX6-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE.ZIP"; $output = $filename; }
elsif ($package eq "PX7LITE") { $filename = "PX7-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN.ZIP"; $output = $filename; }
elsif ($package eq "PX8LITE") { $filename = "PX8-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN.ZIP"; $output = $filename; }
elsif ($package eq "PX9LITE") { $filename = "PX9-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT.ZIP"; $output = $filename; }
elsif ($package eq "PX10LITE") { $filename = "PX10-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT-RESIDENTIAL.ZIP"; $output = $filename; }
elsif ($package eq "PX1LITEBIN") { $filename = "PX1-LITE-IP-COUNTRY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX2LITEBIN") { $filename = "PX2-LITE-IP-PROXYTYPE-COUNTRY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX3LITEBIN") { $filename = "PX3-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX4LITEBIN") { $filename = "PX4-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX5LITEBIN") { $filename = "PX5-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX6LITEBIN") { $filename = "PX6-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX7LITEBIN") { $filename = "PX7-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX8LITEBIN") { $filename = "PX8-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX9LITEBIN") { $filename = "PX9-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX10LITEBIN") { $filename = "PX10-LITE-IP-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT-RESIDENTIAL.BIN.ZIP"; $output = $filename; }
elsif ($package eq "PX1IPV6") { $filename = "PX1-IPV6-COUNTRY.ZIP"; $output = $filename; }
elsif ($package eq "PX2IPV6") { $filename = "PX2-IPV6-PROXYTYPE-COUNTRY.ZIP"; $output = $filename; }
elsif ($package eq "PX3IPV6") { $filename = "PX3-IPV6-PROXYTYPE-COUNTRY-REGION-CITY.ZIP"; $output = $filename; }
elsif ($package eq "PX4IPV6") { $filename = "PX4-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP.ZIP"; $output = $filename; }
elsif ($package eq "PX5IPV6") { $filename = "PX5-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN.ZIP"; $output = $filename; }
elsif ($package eq "PX6IPV6") { $filename = "PX6-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE.ZIP"; $output = $filename; }
elsif ($package eq "PX7IPV6") { $filename = "PX7-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN.ZIP"; $output = $filename; }
elsif ($package eq "PX8IPV6") { $filename = "PX8-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN.ZIP"; $output = $filename; }
elsif ($package eq "PX9IPV6") { $filename = "PX9-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT.ZIP"; $output = $filename; }
elsif ($package eq "PX10IPV6") { $filename = "PX10-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT-RESIDENTIAL.ZIP"; $output = $filename; }
elsif ($package eq "PX1LITEIPV6") { $filename = "PX1-LITE-IPV6-COUNTRY.ZIP"; $output = $filename; }
elsif ($package eq "PX2LITEIPV6") { $filename = "PX2-LITE-IPV6-PROXYTYPE-COUNTRY.ZIP"; $output = $filename; }
elsif ($package eq "PX3LITEIPV6") { $filename = "PX3-LITE-IPV6-PROXYTYPE-COUNTRY-REGION-CITY.ZIP"; $output = $filename; }
elsif ($package eq "PX4LITEIPV6") { $filename = "PX4-LITE-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP.ZIP"; $output = $filename; }
elsif ($package eq "PX5LITEIPV6") { $filename = "PX5-LITE-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN.ZIP"; $output = $filename; }
elsif ($package eq "PX6LITEIPV6") { $filename = "PX6-LITE-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE.ZIP"; $output = $filename; }
elsif ($package eq "PX7LITEIPV6") { $filename = "PX7-LITE-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN.ZIP"; $output = $filename; }
elsif ($package eq "PX8LITEIPV6") { $filename = "PX8-LITE-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN.ZIP"; $output = $filename; }
elsif ($package eq "PX9LITEIPV6") { $filename = "PX9-LITE-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT.ZIP"; $output = $filename; }
elsif ($package eq "PX10LITEIPV6") { $filename = "PX10-LITE-IPV6-PROXYTYPE-COUNTRY-REGION-CITY-ISP-DOMAIN-USAGETYPE-ASN-LASTSEEN-THREAT-RESIDENTIAL.ZIP"; $output = $filename; }
elsif ($package eq "DBASNLITE") { $filename = "IP2LOCATION-LITE-ASN.ZIP"; $output = $filename; }
else {
	print STDERR "\n[Error] Unknown -package command line parameter.\n\n";
	exit(0);
}

if ($opt_output ne "") {
	$output = $opt_output;
}

&check_info();
&download();
&check_update();

sub check_info() {
	my $localpackage = $package;

	if ($package eq "DB1CIDR") {
		$localpackage = "DB1";
	} elsif ($package eq "DB1ACL") {
		$localpackage = "DB1";
	} elsif ($package eq "DB1CIDRIPV6") {
		$localpackage = "DB1";
	} elsif ($package eq "DB1ACLIPV6") {
		$localpackage = "DB1";
	}

	my $ua = LWP::UserAgent->new(
    ssl_opts => {
        verify_hostname => 0
    }
	);
	if ($proxy ne "") {
		$ua->proxy(['http', 'https'], $proxy);
	}

	my %form;

	$form{'email'} = $login;
	$form{'password'} = $password;
	$form{'token'} = $token;
	$form{'productcode'} = $localpackage;

	my $response = $ua->post($urlinfo, \%form);

	if ($response->is_success) {
	} else {
		die "\n[Error] Error while verifying account. (" . $response->status_line . ")  ($VERSION)\n";
	}

	my $message = $response->content();

	my @data = split(/\;/, $message);

	if (!defined($data[0])) {
		print STDERR "\n[Error] No information data. Please contact support\@ip2location.com. ($VERSION)\n";
		exit(0);
	} else {
		if ($data[0] eq "OK") {
			$total_size = $data[3];
			$expiry_date = $data[1];
			$database_version = $data[2];
		} elsif ($data[0] eq "EXPIRED") {
			print "\n[Error] This download account has been expired since $data[1]. Please visit https://www.ip2location.com to renew the subscription.\n";
			exit(0);
		} elsif ($data[0] eq "INVALID") {
			print "\n[Error] Invalid account name or password.";
			exit(0);
		} elsif ($data[0] eq "NOPERMISSION") {
			print "\n[Error] This download account or token could not download database due to permission issue.\n";
			exit(0);
		} else {
			print "\n[Error] Unknown issue [$message]. Please contact support\@ip2location.com. ($VERSION)\n";
			exit(0);
		}
	}
}

sub download() {
	print_header();
	print STDERR "Downloading ", $output, " ...\n";

	my $ua;
	my $response;

	$ua = LWP::UserAgent->new(
    ssl_opts => {
        verify_hostname => 0
    }
	);
	if ($proxy ne "") {
		$ua->proxy(['http', 'https'], $proxy);
	}
	push @{ $ua->requests_redirectable }, 'POST';

	my %form;

	$form{'login'} = $login;
	$form{'password'} = $password;
	$form{'token'} = $token;
	$form{'productcode'} = $package;
	$form{'source'} = "perl-download-$VERSION";
	$form{'btnDownload'} = "btnDownload";

	$response = $ua->post($url, \%form, ':content_cb' => \&callback );

	if ($response->is_success) {
		open OUT1, ">$output" or die "\n[Error] Unable to write $output to drive. Please check the file system permission or free diskspace. ($VERSION)\n";
		binmode(OUT1);
		print OUT1 $final_data;
		close OUT1;

		my $filesize = -s "$output";
		if ($filesize != $total_size) {
			print STDERR "\n\n[Error] Incorrect file size of $output. ($VERSION)\n";
		}
	} else {
		print STDERR  "\n\n[Error] Error while downloading. ($response->status_line) ($VERSION)\n";
	}
}

sub check_update() {
	my $ua;
	my $response;
	my $message;
	$ua = LWP::UserAgent->new(
    ssl_opts => {
        verify_hostname => 0
    }
	);
	if ($proxy ne "") {
		$ua->proxy(['http', 'https'], $proxy);
	}
	$response = $ua->get($urlversion);
	$message = $response->content();
	my $newversion = $message;
	$newversion =~ s/\n//g;

	my $thisversion = $VERSION;
	$thisversion =~ s/\.//g;
	$message =~ s/\.//g;

	if ($message > $thisversion) {
		print STDERR "\n[IMPORTANT] New script version $newversion detected. Please download the latest version from < URL: https://www.ip2location.com/downloads/ip2location-downloader.zip >. \n";
	}
}

sub callback {
   my ($data, $response, $protocol) = @_;
   $final_data .= $data;
   print progress_bar( length($final_data), $total_size, 25, '=' );
}

sub progress_bar {
    my ( $got, $total, $width, $char ) = @_;
    $width ||= 25; $char ||= '=';
    my $num_width = length($total);
    sprintf "|%-${width}s| Got %${num_width}s bytes of %s (%.2f%%)\r",
        $char x (($width-1)*$got/$total). '>',
        $got, $total, 100*$got/+$total;
}

sub  print_help {
	print_header();
	print <<HELP
This program download the latest database from IP2Location.com.

Command Line Syntax:
$0 -package <package> -token <token> -login <login> -password <password>
            -output <output>  -proxy <proxy_server> -ssl

  package  - Database Package (Example: DB24, DB24BIN, DB24IPV6, DB24BINIPV6,
                                        DB11LITE, DB11LITEBIN, DB11LITEIPV6,
                                        DB11LITEBINIPV6, PX10, PX10BIN, PX10IPV6
                                        PX10LITE, PX10LITEBIN, PX10LITEIPV6 or
                                        DBASNLITE)
  token    - Download Token
  login    - Login (Deprecated - Use -token)
  password - Password (Deprecated - Use -token)
  proxy    - Proxy Server with Port (Optional)
  output   - Output Filename (Optional)
  showall  - Show All Package Code (Optional)
  ssl      - Download via SSL (Default); May require additional libraries.

Please contact support\@ip2location.com for technical support.

HELP
}

sub  print_header {
	print <<HEADER
------------------------------------------------------------------------
IP2Location Download Client (Version $VERSION)
https://www.ip2location.com
------------------------------------------------------------------------
HEADER
}

sub  print_showall {
	print_header();
	print <<SHOWALL
Below are all product codes supported by this download script.

DB1, DB2, DB3, DB4, DB5, DB6, DB7, DB8, DB9, DB10, DB11, DB12, DB13, DB14, DB15, DB16, DB17, DB18, DB19, DB20, DB21, DB22, DB23, DB24, DB1BIN, DB2BIN, DB3BIN, DB4BIN, DB5BIN, DB6BIN, DB7BIN, DB8BIN, DB9BIN, DB10BIN, DB11BIN, DB12BIN, DB13BIN, DB14BIN, DB15BIN, DB16BIN, DB17BIN, DB18BIN, DB19BIN, DB20BIN, DB21BIN, DB22BIN, DB23BIN, DB24BIN, DB1CIDR, DB1ACL, DB1LITE, DB3LITE, DB5LITE, DB9LITE, DB11LITE, DB1LITEBIN, DB3LITEBIN, DB5LITEBIN, DB9LITEBIN, DB11LITEBIN, DB1IPV6, DB2IPV6, DB3IPV6, DB4IPV6, DB5IPV6, DB6IPV6, DB7IPV6, DB8IPV6, DB9IPV6, DB10IPV6, DB11IPV6, DB12IPV6, DB13IPV6, DB14IPV6, DB15IPV6, DB16IPV6, DB17IPV6, DB18IPV6, DB19IPV6, DB20IPV6, DB21IPV6, DB22IPV6, DB23IPV6, DB24IPV6, DB1BINIPV6, DB2BINIPV6, DB3BINIPV6, DB4BINIPV6, DB5BINIPV6, DB6BINIPV6, DB7BINIPV6, DB8BINIPV6, DB9BINIPV6, DB10BINIPV6, DB11BINIPV6, DB12BINIPV6, DB13BINIPV6, DB14BINIPV6, DB15BINIPV6, DB16BINIPV6, DB17BINIPV6, DB18BINIPV6, DB19BINIPV6, DB20BINIPV6, DB21BINIPV6, DB22BINIPV6, DB23BINIPV6, DB24BINIPV6, DB1CIDRIPV6, DB1ACLIPV6, DB1LITEIPV6, DB3LITEIPV6, DB5LITEIPV6, DB9LITEIPV6, DB11LITEIPV6, DB1LITEBINIPV6, DB3LITEBINIPV6, DB5LITEBINIPV6, DB9LITEBINIPV6, DB11LITEBINIPV6, PX1, PX2, PX3, PX4, PX5, PX6, PX7, PX8, PX9, PX10, PX1BIN, PX2BIN, PX3BIN, PX4BIN, PX5BIN, PX6BIN, PX7BIN, PX8BIN, PX9BIN, PX10BIN, PX1LITE, PX2LITE, PX3LITE, PX4LITE, PX5LITE, PX6LITE, PX7LITE, PX8LITE, PX1LITEBIN, PX2LITEBIN, PX3LITEBIN, PX4LITEBIN, PX5LITEBIN, PX6LITEBIN, PX7LITEBIN, PX8LITEBIN, PX9LITEBIN, PX10LITEBIN, PX1IPV6, PX2IPV6, PX3IPV6, PX4IPV6, PX5IPV6, PX6IPV6, PX7IPV6, PX8IPV6, PX1LITEIPV6, PX2LITEIPV6, PX3LITEIPV6, PX4LITEIPV6, PX5LITEIPV6, PX6LITEIPV6, PX7LITEIPV6, PX8LITEIPV6, PX9LITEIPV6, PX10LITEIPV6, DBASNLITE

Please contact support\@ip2location.com for technical support.

SHOWALL
}