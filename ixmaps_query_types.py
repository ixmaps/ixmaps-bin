from ixmaps_query_format_functions import *

query_types = {

    "all_submitters": QueryInfo (
        title = "Submitters",
        query = """select submitter as "Submitter", count(*) as "Count" from traceroute group by submitter order by submitter""",
        header = """<p>To view this data graphically, you must have <a href="http://earth.google.com/download-earth.html">Google Earth</a> downloaded and installed :</p>
            <ol><li>click on: any submitter name (eg AndrewC).</li>
            <li>click on: any id number (eg 1874 2009-12-13 12:15 M5S2M8 www.wikipedia.com [208.80.152.2])</li>
            <li>On the Traceroute Detail page - on the top line Google Earth is hyperlinked - select it and Google Earth will automatically launch the visualization</li></ol>""",
        footer = """<br/>This product includes GeoLite data created by MaxMind, available from
            <a href="http://maxmind.com/">http://maxmind.com/</a>
            <br><br>""",
        link_to = "submitter",
        # generic_headers_link_to = "/faq.php#",
        # specific_headers_link_to = {
            # 'Count' : "http://slashdot.org/"
            # }
        ),

    "all_zip_codes": QueryInfo (
        query = """select zip_code as "Zip Code",
        count(*) as "Count"
        from traceroute group by zip_code order by zip_code""",
        link_to = "zip_code",
        # custom_table_function = html_traceroute_details
        ),

    "submitter": QueryInfo (
        title = "Available Traceroutes",

        header = "<p>Traceroutes submitted for user %s</p>",

        custom_table_function = html_submitter_table,

        # --- Get a list of traceroutes with their associated countries--
        #     including zero countries (takes some finagling...) ---
        query = """/** Select all traceroutes (and traits) for a particular submitter
            (or zip code), including traceroutes with zero countries **/ 
            (
                /** Select all traceroutes, for a particular submitter (or zip code),
                    in cases where not a single IP is going through a known country **/
                select TR.id as "ID",
                'xx' as " ",
                sub_time as "Date/Time", 
                zip_code as "Zip Code",
                TR.dest as "Destination",
                dest_ip as "Destination IP",
                nsa, hotel
                from traceroute TR, traceroute_traits TRT 
                where
                (
                    /** Select all traceroute-IDs, for a particular submitter/zip-code,
                        that contain no known countries **/
                    TR.id not in
                    (
                        /** Select all traceroute-IDs, for a particular submitter/zip-code,
                            which do go through known countries **/
                        select TR.id from traceroute TR, traceroute_traits TRT, traceroute_countries TRC
                        where
                        (
                            TR.id = TRT.id
                            and TR.id = TRC.traceroute_id 
                            and submitter='%s'
                        )
                    )
                    and TR.id = TRT.id
                    and submitter='%s'
                )
            )
            union
            (
                /** Select all traceroutes, for a particular submitter/zip-code, and
                    each country that it goes through **/
                select TR.id, TRC.country_code, sub_time, zip_code, TR.dest,
                dest_ip, nsa, hotel
                from traceroute TR, traceroute_traits TRT, traceroute_countries TRC
                where
                (
                    TR.id = TRT.id 
                    and TR.id = TRC.traceroute_id 
                    and submitter='%s' 
                )
            )
            order by 1""",
        link_to = "traceroute_id",
        footer = (html_legend ( )
                  + """This product includes GeoLite data created by MaxMind, available from
            <a href="http://maxmind.com/">http://maxmind.com/</a>
            <br><br><a href="http://ixmaps.ischool.utoronto.ca/cgi-bin/tr-detail-tech.cgi?traceroute_id=0"> Technical version </href>"""),
        ),

    "zip_code": QueryInfo (
        title = "Available Traceroutes",
        # --- Get a list of traceroutes with their associated countries--
        #     including zero countries (takes some finagling...) ---
        query = """/** Select all traceroutes (and traits) for a particular sumbitter
            (or zip code), including traceroutes with zero countries **/ 
            (
                /** Select all traceroutes, for a particular submitter (or zip code),
                    in cases where not a single IP is going through a known country **/
                select TR.id as "ID",
                'xx' as " ",
                sub_time as "Date/Time",
                submitter as "Submitter",
                dest as "Destination",
                dest_ip as "Destination IP"
                from traceroute TR, traceroute_traits TRT 
                where
                (
                    /** Select all traceroute-IDs, for a particular submitter/zip-code,
                        that contain no known countries **/
                    TR.id not in
                    (
                        /** Select all traceroute-IDs, for a particular submitter/zip-code,
                            which do go through known countries **/
                        select TR.id from traceroute TR, traceroute_traits TRT, traceroute_countries TRC
                        where
                        (
                            TR.id = TRT.id
                            and TR.id = TRC.traceroute_id 
                            and zip_code='%s'
                        )
                    )
                    and TR.id = TRT.id
                    and zip_code='%s'
                )
            )
            union
            (
                /** Select all traceroutes, for a particular submitter/zip-code, and
                    each country that it goes through **/
                /*TR.*, TRT.*, TRC.country_code */
                select TR.id, country_code, sub_time, submitter, dest,dest_ip
                from traceroute TR, traceroute_traits TRT, traceroute_countries TRC
                where
                (
                    TR.id = TRT.id 
                    and TR.id = TRC.traceroute_id 
                    and zip_code='%s' 
                )
            )
            order by 1""",

        link_to = "traceroute_id",
        ),

    "traceroute_id": QueryInfo (

        title = "Traceroute detail",

        header = """<table border="0" width="100%%">
          <tr>
            <td width="1">Traceroute&nbsp;id:</td> 
            <td>
              <b>%s</b> 
            </td>
            <td colspan="3" align="right"> <a href="./ge-render.cgi?traceroute_id=%s"> <b>Open in Google Earth</b> </a> </td> 
          </tr>
          <tr>
            <td>
              Origin:
            </td>
            <td>
              <b>%s</b>
            </td>
            <td width='1'>
              Destination:
            </td>
            <td>
              <b>%s</b> [%s]
            </td>
            <td width='150'>
              &nbsp;
            </td>
          </tr>
          <tr>
            <td>
              Submitted by:
            </td>
            <td>
              %s
            </td>
            <td>
              Submitted&nbsp;on:
            </td>
            <td>
              %s
            </td>
            <td>
              &nbsp;
            </td>

          </tr>
        </table>
        <br />
          """,


        query = """select attempt,
            hop as "Hop",
            ip_addr_info.ip_addr as "IP Address",
            mm_country as " ",
            rtt_ms as "Min. Latency",
            name as "Carrier",
            mm_city as "Location",
            gl_override as "GeoPrecision",
            hostname as "Hostname",
            lat, long, mm_region from tr_item, ip_addr_info,
            as_users where traceroute_id=%s and
            tr_item.ip_addr=ip_addr_info.ip_addr and asnum=num order
            by hop, attempt""",

        generic_headers_link_to = "/faq.php#",

        specific_headers_link_to = {
            'Location' :    "http://maps.google.ca/",
            'GeoPrecision': "http://ixmaps.ischool.utoronto.ca/technical.html",
            },

        custom_page_function = html_traceroute_details_page,

        custom_table_function = html_traceroute_details,

        footer = (html_legend ( )
                  + """This product includes GeoLite data created by MaxMind, available from
            <a href="http://maxmind.com/">http://maxmind.com/</a><br /><br />
            <a href='./tr-query.cgi?query_type=traceroute_id--geek_version&arg=%s'>
            Technical version</a>
            """ ),
        ),


    "traceroute_id--geek_version": QueryInfo (
        title = "Traceroute detail--technical version",

        header = """<table border="0" width="100%%">
          <tr>
            <td width="1">Traceroute&nbsp;id:</td> 
            <td>
              <b>%s</b> 
            </td>
            <td colspan="3" align="right"> <a href="./ge-render.cgi?traceroute_id=%s"> <b>Open in Google Earth</b> </a> </td> 
          </tr>
          <tr>
            <td>
              Origin:
            </td>
            <td>
              <b>%s</b>
            </td>
            <td width='1'>
              Destination:
            </td>
            <td>
              <b>%s</b> [%s]
            </td>
            <td width='150'>
              &nbsp;
            </td>
          </tr>
          <tr>
            <td>
              Submitted by:
            </td>
            <td>
              %s
            </td>
            <td>
              Submitted&nbsp;on:
            </td>
            <td>
              %s
            </td>
            <td>
              &nbsp;
            </td>

          </tr>
        </table>
        <br />
          """,

        # generic_headers_link_to = "/faq.php#",

        query = """select attempt,
            hop as "Hop",
            ip_addr_info.ip_addr as "IP Address",
            rtt_ms as "Round Trip Times",
            asnum as "AS#",
            lat as "Latitude",
            long as "Longitude",
            hostname as "Hostname"
            from tr_item, ip_addr_info where traceroute_id=%s and
            tr_item.ip_addr=ip_addr_info.ip_addr order by hop,
            attempt""",

        footer = """<br/>This product includes GeoLite data created by MaxMind, available from
            <a href="http://maxmind.com/">http://maxmind.com/</a><br /><br />
            <a href='./tr-query.cgi?query_type=traceroute_id&arg=%s'>
            Standard version</a>
            """,

        # multi_field = "Round trip times",

        custom_page_function = html_traceroute_details_page,

        custom_table_function = html_traceroute_details_geek,
        ),

    "just_canada": QueryInfo (
        query = """SELECT distinct traceroute.* FROM ca_origin_and_destination, traceroute 
            WHERE ca_origin_and_destination.traceroute_id = traceroute.id""",

        # query = """/** Select all traceroutes, that remain solely in Canada **/
            # select TR.*, TRT.*, TRC.country_code 
            # from traceroute TR, traceroute_traits TRT, traceroute_countries TRC
            # where
              # ( TR.id = TRT.id 
                # and TR.id = TRC.traceroute_id 
                # and country_code = 'CA')""",

        link_to = "traceroute_id"
        ),

#     "boomerang": QueryInfo (
#         query = """SELECT distinct traceroute.* FROM boomerang_routes, traceroute 
#                    WHERE boomerang_routes.id = traceroute.id""",
#         link_to = "traceroute_id"
#         ),
               
    "boomerang": QueryInfo (
        query = """
select 
  traceroute_id as "ID",
  hop as "Hop",
  ip_addr as "IP Address",
  hostname as "Hostname",
  asnum as "AS#", 
  mm_lat,
  mm_long,
  lat as "Longitude",
  long as "Longitude",
  mm_city as "City",
  mm_region as "Region",
  mm_country as "Country",
  mm_postal as "Postal code",
  dest as "Destination",
  dest_ip as "Destination IP"
from 
  (
    select 
      temp_full_routes_large.* 
    from
      (
        select
          TI.traceroute_id, TI.hop, 
          IP.ip_addr, IP.hostname, IP.asnum, IP.mm_lat, IP.mm_long, IP.lat,
          IP.long,IP.mm_city, IP.mm_region, IP.mm_country, IP.mm_postal,
          TR.dest, TR.dest_ip
        from 
          ip_addr_info IP, 
          tr_item      TI, 
          traceroute   TR
        where (
          IP.ip_addr=TI.ip_addr     and
          TR.id = TI.traceroute_id  and
          attempt = 1 )    
      )
      temp_full_routes_large 
    join 
      (
        select 
          traceroute_id 
        from 
          ( 
            select * from 
            (
              select 
                temp1.*, traceroute.dest, traceroute.dest_ip 
              from 
                (
                  select
                    t.traceroute_id, t.hop, i.ip_addr, i.hostname, i.asnum, i.mm_lat,
                    i.mm_long, i.lat, i.long,i.mm_city, i.mm_region, i.mm_country, 
                    i.mm_postal
                  from 
                    ip_addr_info as i join tr_item as t 
                    on i.ip_addr=t.ip_addr 
                  where attempt=1
                )
                temp1 
              join traceroute on temp1.traceroute_id=traceroute.id
            )
            temp_full_routes_large where hop=1 and mm_country='CA'
          )
          temp_ca_origin
        join 
          (
            select 
              id, dest, mm_country 
            from 
              traceroute 
            join
              ip_addr_info on dest_ip=ip_addr 
            where 
              mm_country='CA'
          )
          temp_ca_destination 
        on 
          traceroute_id=id 
        order by 
          traceroute_id
      )
      temp3 
    on
      temp_full_routes_large.traceroute_id=temp3.traceroute_id 
    order by
      temp_full_routes_large.traceroute_id
  )
  temp_ca_origin_and_destination 
join
  (
    select distinct 
      traceroute_id as id
    from
      (
        select 
          temp_full_routes_large.* 
        from
          (
            select
              TI.traceroute_id, TI.hop, 
              IP.ip_addr, IP.hostname, IP.asnum, IP.mm_lat, IP.mm_long, IP.lat,
              IP.long,IP.mm_city, IP.mm_region, IP.mm_country, IP.mm_postal,
              TR.dest, TR.dest_ip
            from 
              ip_addr_info IP, 
              tr_item      TI, 
              traceroute   TR
            where (
              IP.ip_addr=TI.ip_addr     and
              TR.id = TI.traceroute_id  and
              attempt = 1 )    
          )
          temp_full_routes_large 
        join 
          (
            select 
              traceroute_id 
            from 
              ( 
                select * from 
                (
                  select 
                    temp1.*, traceroute.dest, traceroute.dest_ip 
                  from 
                    (
                      select
                        t.traceroute_id, t.hop, i.ip_addr, i.hostname, i.asnum, i.mm_lat,
                        i.mm_long, i.lat, i.long,i.mm_city, i.mm_region, i.mm_country, 
                        i.mm_postal
                      from 
                        ip_addr_info as i join tr_item as t 
                        on i.ip_addr=t.ip_addr 
                      where attempt=1
                    )
                    temp1 
                  join traceroute on temp1.traceroute_id=traceroute.id
                )
                temp_full_routes_large where hop=1 and mm_country='CA'
              )
              temp_ca_origin
            join 
              (
                select 
                  id, dest, mm_country 
                from 
                  traceroute 
                join
                  ip_addr_info on dest_ip=ip_addr 
                where 
                  mm_country='CA'
              )
              temp_ca_destination 
            on 
              traceroute_id=id 
            order by 
              traceroute_id
          )
          temp3 
        on
          temp_full_routes_large.traceroute_id=temp3.traceroute_id 
        order by
          temp_full_routes_large.traceroute_id
      )
      temp_ca_origin_and_destination 
    where 
      mm_country='US'
  )
  temp4 
on 
  temp_ca_origin_and_destination.traceroute_id=temp4.id 
order by
  temp_ca_origin_and_destination.traceroute_id,hop
""",
        link_to = "traceroute_id",
),

#    "nsa": QueryInfo (
#        query = """SELECT distinct traceroute.* FROM boomerang_routes, traceroute 
#                   WHERE boomerang_routes.id = traceroute.id""",
#        link_to = "traceroute_id"
#        ),

        
}

