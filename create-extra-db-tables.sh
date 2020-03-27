#!/bin/bash

#This script is designed to generate a bunch of useful tables to the IXmaps db - ones that (currently) are not otherwise being created
#Yes, all of these queries can be done in one line of SQL. I'm going for clarity here, I guess (?)

#Current list of suspected NSA cities - update as appropriate

#NSA_cities="mm_city like '%San Francisco%' or mm_city like '%Los Angeles%' or mm_city like '%New York%' or mm_city like '%Chicago%' or mm_city like '%Dallas%' or mm_city like '%Atlanta%' or mm_city like '%Washington%' or mm_city like '%Seattle%' or mm_city like '%San Jose%' or mm_city like '%San Diego%' or mm_city like '%Miami%' or mm_city like '%Boston%' or mm_city like '%Phoenix%' or mm_city like '%Salt Lake City%' or mm_city like '%Nashville%' or mm_city like '%Denver%' or mm_city like '%Portland%' or mm_city like '%St Louis%' or mm_city like '%Bluffdale%' or mm_city like '%Houston%'"



#echo "This script is designed to create some useful extra tables in the IXmaps database"
#if [ -z "$1" ]; then
#	echo -e "Do you want to drop old versions of the tables? (y/n) \c"
#	read input
#else
#	input=$1
#fi
#if [ $input = "y" ]; then
    psql ixmaps -c "drop table if exists full_routes;"
    psql ixmaps -c "drop table if exists full_routes_last_hop;"
    psql ixmaps -c "drop table if exists ca_origin;"
    psql ixmaps -c "drop table if exists ca_destination;"
    psql ixmaps -c "drop table if exists ca_origin_ca_destination;"
    psql ixmaps -c "drop table if exists boomerang_routes;"
    psql ixmaps -c "drop table if exists non_boomerang_routes;"
    psql ixmaps -c "drop table if exists nsa_routes;"
    psql ixmaps -c "drop table if exists ca_to_ca_nsa;"
    psql ixmaps -c "drop table if exists ca_to_ca_non_nsa;"
    psql ixmaps -c "drop table if exists us_origin;"
    psql ixmaps -c "drop table if exists us_destination;"
    psql ixmaps -c "drop table if exists us_origin_us_destination;"
    psql ixmaps -c "drop table if exists us_to_us_nsa;"
    psql ixmaps -c "drop table if exists us_to_us_non_nsa;"
    psql ixmaps -c "drop table if exists ca_origin_us_destination;"
    psql ixmaps -c "drop table if exists ca_origin_traverses_us;"
#else
#    echo "If the script fails, please rerun and choose to drop old tables"
#fi

# SHORTCUT HERE = attempt=1
echo ""
echo "Generating full_routes_last_hop..."
psql ixmaps -c "select t.traceroute_id,t.hop,i.ip_addr,i.hostname,i.asnum,i.mm_lat,i.mm_long,i.lat,i.long,i.mm_city,i.mm_region,i.mm_country,i.mm_postal,i.gl_override into script_temp1 from
ip_addr_info as i join tr_item as t on i.ip_addr=t.ip_addr where attempt=1;"
psql ixmaps -c "select script_temp1.*,traceroute.dest,traceroute.dest_ip,traceroute.sub_time,traceroute.submitter,traceroute.zip_code into script_temp2 from script_temp1 join traceroute on script_temp1.traceroute_id=traceroute.id;"
psql ixmaps -c "select script_temp2.*,as_users.short_name into full_routes from script_temp2 join as_users on script_temp2.asnum=as_users.num order by traceroute_id,hop;"
psql ixmaps -c "select f.*,l.hop_lh,l.reached into full_routes_last_hop from full_routes as f join tr_last_hops as l on
f.traceroute_id = l.traceroute_id_lh;"
# the difference between full_routes and full_routes_last_hop is that last hop data is only included in the _last_hop one. Therefore, due to the join type, some routes will be omitted from _last_hop. In other words, full_routes.count >= full_routes_last_hop.count

# SHORTCUT HERE - hop=1
echo ""
echo "Generating ca_origin..."
psql ixmaps -c "select * into ca_origin from full_routes_last_hop where hop=1 and mm_country='CA';"

echo ""
echo "Generating ca_destination..."
#psql ixmaps -c "select id,dest,mm_country into ca_destination from traceroute join ip_addr_info on dest_ip=ip_addr where mm_country='CA';"
# NOW USING LAST HOP IP ADDR INSTEAD OF DESTINATION IP ADDR
psql ixmaps -c "select traceroute_id_lh,mm_country into ca_destination from tr_last_hops join ip_addr_info on ip_addr_lh=ip_addr where mm_country='CA';"
psql ixmaps -c "alter table ca_destination rename column traceroute_id_lh to id;"

echo ""
echo "Generating ca_origin_ca_destination..."
psql ixmaps -c "select traceroute_id into script_temp3 from ca_origin join ca_destination on traceroute_id=id order by traceroute_id;"
psql ixmaps -c "select full_routes_last_hop.* into ca_origin_ca_destination from full_routes_last_hop join script_temp3 on
full_routes_last_hop.traceroute_id=script_temp3.traceroute_id order by full_routes_last_hop.traceroute_id, full_routes_last_hop.hop;"

# we are now ignoring any routes with generic locations. Therefore, count of boom + non_boom != ca_ori_ca_dest
# think about including 37.751, the new maxmind generic location
echo ""
echo "Generating boomerang_routes..."
psql ixmaps -c "select * into boomerang_routes from ca_origin_ca_destination where traceroute_id in (select distinct traceroute_id from ca_origin_ca_destination where mm_country='US' and lat!=38);"
#psql ixmaps -c "alter table boomerang_routes drop column traceroute_id;"

echo ""
echo "Generating non_boomerang_routes..."
psql ixmaps -c "select * into non_boomerang_routes from ca_origin_ca_destination where traceroute_id not in (select distinct traceroute_id from ca_origin_ca_destination where mm_country='US');"

echo ""
echo "Generating nsa_routes..."
psql ixmaps -c "select distinct traceroute_id into script_temp4_1 from full_routes_last_hop where mm_city like '%San Francisco%' or mm_city like '%Los Angeles%' or mm_city like '%New York%' or mm_city like '%Chicago%' or mm_city like '%Dallas%' or mm_city like '%Atlanta%' or mm_city like '%Washington%' or mm_city like '%Ashburn%' or mm_city like '%Seattle%' or mm_city like '%San Jose%' or mm_city like '%San Diego%' or mm_city like '%Miami%' or mm_city like '%Boston%' or mm_city like '%Phoenix%' or mm_city like '%Salt Lake City%' or mm_city like '%Nashville%' or mm_city like '%Denver%' or mm_city like '%Portland%' or mm_city like '%St Louis%' or mm_city like '%Bluffdale%' or mm_city like '%Houston%';"
psql ixmaps -c "alter table script_temp4_1 rename column traceroute_id to id;"
psql ixmaps -c "select * into nsa_routes from script_temp4_1 join full_routes_last_hop on script_temp4_1.id = full_routes_last_hop.traceroute_id order by traceroute_id,hop;"

echo ""
echo "Generating ca_to_ca_nsa..."
psql ixmaps -c "select distinct traceroute_id into script_temp4 from ca_origin_ca_destination where mm_city like '%San Francisco%' or mm_city like '%Los Angeles%' or mm_city like '%New York%' or mm_city like '%Chicago%' or mm_city like '%Dallas%' or mm_city like '%Atlanta%' or mm_city like '%Washington%' or mm_city like '%Ashburn%' or mm_city like '%Seattle%' or mm_city like '%San Jose%' or mm_city like '%San Diego%' or mm_city like '%Miami%' or mm_city like '%Boston%' or mm_city like '%Phoenix%' or mm_city like '%Salt Lake City%' or mm_city like '%Nashville%' or mm_city like '%Denver%' or mm_city like '%Portland%' or mm_city like '%St Louis%' or mm_city like '%Bluffdale%' or mm_city like '%Houston%';"
psql ixmaps -c "alter table script_temp4 rename column traceroute_id to id;"
psql ixmaps -c "select * into ca_to_ca_nsa from script_temp4 join ca_origin_ca_destination on script_temp4.id = ca_origin_ca_destination.traceroute_id order by traceroute_id,hop;"

echo ""
echo "Generating ca_to_ca_non_nsa..."
psql ixmaps -c "select traceroute_id into script_temp5 from ca_origin_ca_destination except select id from script_temp4;"
psql ixmaps -c "alter table script_temp5 rename column traceroute_id to id;"
psql ixmaps -c "select * into ca_to_ca_non_nsa from script_temp5 join ca_origin_ca_destination on script_temp5.id = ca_origin_ca_destination.traceroute_id order by traceroute_id,hop;"

echo ""
echo "Generating us_origin..."
psql ixmaps -c "select * into us_origin from full_routes_last_hop where hop=1 and mm_country='US';"

echo ""
echo "Generating us_destination..."
#psql ixmaps -c "select id,dest,mm_country into us_destination from traceroute join ip_addr_info on dest_ip=ip_addr where mm_country='US';"
psql ixmaps -c "select traceroute_id_lh,mm_country into us_destination from tr_last_hops join ip_addr_info on ip_addr_lh=ip_addr where mm_country='US';"
psql ixmaps -c "alter table us_destination rename column traceroute_id_lh to id;"

echo ""
echo "Generating us_origin_us_destination..."
psql ixmaps -c "select traceroute_id into script_temp6 from us_origin join us_destination on traceroute_id=id order by traceroute_id;"
psql ixmaps -c "select full_routes_last_hop.* into us_origin_us_destination from full_routes_last_hop join script_temp6 on
full_routes_last_hop.traceroute_id=script_temp6.traceroute_id order by full_routes_last_hop.traceroute_id, full_routes_last_hop.hop;"

echo ""
echo "Generating us_to_us_nsa..."
psql ixmaps -c "select distinct traceroute_id into script_temp7 from us_origin_us_destination where mm_city like '%San Francisco%' or mm_city like '%Los Angeles%' or mm_city like '%New York%' or mm_city
like '%Chicago%' or mm_city like '%Dallas%' or mm_city like '%Atlanta%' or mm_city like '%Washington%' or mm_city like '%Seattle%' or mm_city like '%San Jose%' or mm_city like '%San Diego%' or mm_city
like '%Miami%' or mm_city like '%Boston%' or mm_city like '%Phoenix%' or mm_city like '%Salt Lake City%' or mm_city like '%Nashville%' or mm_city like '%Denver%' or mm_city like '%Portland%' or mm_city
like '%St Louis%' or mm_city like '%Bluffdale%' or mm_city like '%Houston%';"
psql ixmaps -c "alter table script_temp7 rename column traceroute_id to id;"
psql ixmaps -c "select * into us_to_us_nsa from script_temp7 join us_origin_us_destination on script_temp7.id = us_origin_us_destination.traceroute_id order by traceroute_id,hop;"

echo ""
echo "Generating us_to_us_non_nsa..."
psql ixmaps -c "select traceroute_id into script_temp8 from us_origin_us_destination except select id from script_temp7;"
psql ixmaps -c "alter table script_temp8 rename column traceroute_id to id;"
psql ixmaps -c "select * into us_to_us_non_nsa from script_temp8 join us_origin_us_destination on script_temp8.id = us_origin_us_destination.traceroute_id order by traceroute_id,hop;"

echo ""
echo "Generating ca_origin_us_destination..."
psql ixmaps -c "select traceroute_id into script_temp9 from ca_origin join us_destination on traceroute_id=id order by traceroute_id;"
psql ixmaps -c "select full_routes_last_hop.* into ca_origin_us_destination from full_routes_last_hop join script_temp9 on
full_routes_last_hop.traceroute_id=script_temp9.traceroute_id order by full_routes_last_hop.traceroute_id, full_routes_last_hop.hop;"

echo ""
echo "Generating ca_origin_traverses_us..."
psql ixmaps -c "select full_routes_last_hop.* into script_temp10 from full_routes_last_hop join ca_origin on
full_routes_last_hop.traceroute_id=ca_origin.traceroute_id order by full_routes_last_hop.traceroute_id, full_routes_last_hop.hop;"
psql ixmaps -c "select * into ca_origin_traverses_us from script_temp10 where traceroute_id in (select distinct traceroute_id from script_temp10 where mm_country='US' and lat!=38);"

echo ""
echo "Cleaning up temp tables..."
psql ixmaps -c "drop table if exists script_temp1;"
psql ixmaps -c "drop table if exists script_temp2;"
psql ixmaps -c "drop table if exists script_temp3;"
psql ixmaps -c "drop table if exists script_temp4;"
psql ixmaps -c "drop table if exists script_temp4_1;"
psql ixmaps -c "drop table if exists script_temp5;"
psql ixmaps -c "drop table if exists script_temp6;"
psql ixmaps -c "drop table if exists script_temp7;"
psql ixmaps -c "drop table if exists script_temp8;"
psql ixmaps -c "drop table if exists script_temp9;"
psql ixmaps -c "drop table if exists script_temp10;"