from ixmaps import xml_utils
import ixmaps
import sys
import urllib
import re

ICON_PREFIX = "../ge/"
ICON_SUFFIX = '_small.png '

conn = ixmaps.DBConnect.getConnection ( )


class QueryInfo ( ):
    def __init__ (self, query, title="", header="", footer="",
                  link_to="", multi_field=None,
                  custom_table_function=None,
                  custom_page_function=None,
                  generic_headers_link_to='',
                  specific_headers_link_to={} ):


        self.query = query
        self.title = title
        self.header = header
        self.footer = footer
        self.link_to = link_to
        # self.column_to_link = column_to_link
        self.multi_field = multi_field
        self.custom_table_function = custom_table_function
        self.custom_page_function = custom_page_function
        self.generic_headers_link_to = generic_headers_link_to
        self.specific_headers_link_to = specific_headers_link_to
        # self.are_headers_links = are_headers_links
        # self.header_links_exceptions = header_links_exceptions
        # self.headers_link_to = headers_link_to

        

# class QueryInfo ( ):
    # def __init__ (self, query, title="", header="", footer="",
                  # link_to="", column_to_link=""):

        # self.query = query
        # self.title = title
        # self.header = header
        # self.footer = footer
        # self.link_to = link_to
        # self.column_to_link = column_to_link

def html_traceroute_details (field_names, orig_result_list, link_to,
                             generic_headers_link_to, specific_headers_link_to):
    html = xml_utils ( )
    doc = ''

    conn = ixmaps.DBConnect.getConnection ( )
    chotels = ixmaps.CHotels (conn=conn)

    # --- Note: there should be a function to auto-generate these values (es) ---
    attempt_col  = 0
    hop_col      = 1
    ip_col       = 2
    country_col  = 3
    rtt_col      = 4
    city_col     = 6
    override_col = 7
    lat_col      = 9
    long_col     = 10
    region_col   = 11

    result_list = convert_attempts_to_hops_no_rtt (orig_result_list)

    nattempts = len(orig_result_list)
    nhops = result_list[-1][hop_col]
    # nhops = len(result_list)
    rtt = array_2d(nhops,4)
    ipaddrs = array_2d(nhops, nattempts)
    for probe in orig_result_list:
        hop = probe[hop_col]-1
        attempt = probe[attempt_col]-1
        rtt[hop][attempt] = probe[rtt_col]
        ipaddrs[hop][attempt] = probe[ip_col]

    doc += html.tag ("table")
    doc += html.tag ("tr")

    for field in field_names[1:lat_col]:
        if (field in specific_headers_link_to):
            if specific_headers_link_to[field]:
                field = ("<a href='" + specific_headers_link_to[field]
                         + "'>" + field + "</a>")

        elif generic_headers_link_to:
            field = ("<a href='" + generic_headers_link_to +
                     urllib.quote_plus ( str(field) )
                     + "'>" + field + "</a>")

        doc += html.tagged_text ("th", field)

    doc += html.end_tag ("/tr")

    for hop in range ( len (result_list) ):
        record = result_list[hop]
        doc += html.tag ("tr")
        min_latency = get_min_latency(hop, rtt, nhops)

        country_img = ICON_PREFIX + "clear" + ICON_SUFFIX
        chotel_img = ICON_PREFIX + "clear" + ICON_SUFFIX
        nsa_img = ICON_PREFIX + "clear" + ICON_SUFFIX

        is_chotel = ixmaps.is_chotel (
            conn=conn, long_lat=(record[long_col],record[lat_col] ) )

        # --- Assign row-icons ---
        if record[country_col]: country_img = ICON_PREFIX + record[country_col] + ICON_SUFFIX
        if is_chotel: chotel_img = ICON_PREFIX + "carrierhotel" + ICON_SUFFIX
        nsa_img = ICON_PREFIX + get_nsa_flag (
            conn=conn, long_lat=(record[long_col],record[lat_col] ) ) + ICON_SUFFIX

        for item_num in range (1, len(record) ):
            if item_num == country_col:
                doc += html.tag ('td align="center" style="white-space:nowrap"')

                doc += html.empty_tag ('img width="10" src="' + country_img + '"', 
                               'img width="10" src="' + chotel_img + '"',
                               'img width="10" src="' + nsa_img + '"')
                doc += html.end_tag ("/td")

            elif item_num == rtt_col:
                doc += html.tag ("td")
                doc += html.indent (min_latency)
                doc += html.end_tag ("/td")

            elif item_num == city_col:
                doc += html.tag ("td")
                doc += html.text ( record[city_col] )
                doc += html.text ( record[region_col] )
                doc += html.end_tag ("/td")

            elif item_num == override_col:
                geo_precision = get_geo_precision (
                    record[override_col], record[lat_col], record[long_col] )
                doc += html.tag ("td")
                doc += html.indent (geo_precision)
                # doc += html.indent (record[override_col] )
                # doc += html.indent (record[lat_col] )
                # doc += html.indent (record[long_col] )
                doc += html.end_tag ("/td")

            elif (item_num >= lat_col):
                pass

            else:
                doc += html.tagged_text ("td", record[item_num])
        doc += html.end_tag ("/tr")

    doc += html.end_tag ("/table")

    return doc


def html_traceroute_details_geek (field_names, result_list, link_to,
                                  generic_headers_link_to,
                                  specific_headers_link_to ):
    html = xml_utils ( )
    doc = ''

    doc += html.tag ("table")
    doc += html.tag ("tr")

    for field in field_names[1:]:
        if field != 'rtt_ms' and not re.search(r'[Rr]ound.?[Tt]rip', field):
            doc += html.tagged_text ("th", field)
        else:
            doc += html.tagged_text ("th colspan='4'", field)
        

    doc += html.end_tag ("/tr")

    result_list = convert_attempts_to_hops (result_list)

    for record in result_list:
        doc += html.tag ("tr")
        for field in record[1:]:
            doc += html.tagged_text ("td", field)
        doc += html.end_tag ("/tr")

    doc += html.end_tag ("/table")

    return doc

def convert_attempts_to_hops (route_hop_attempts):
    attempt_col = 0
    hop_col = 1

    # --- Note: for this function to work, rttms1_col must be a
    #     greater number than attempt_col and hop_col ---
    rttms1_col = 3

    number_of_attempts = 4
    last_hop = 0
    route_hops = []

    for i in range(len(route_hop_attempts) ):
        orig_row = route_hop_attempts[i]
        hop = orig_row[hop_col]

        # --- If this is a new hop, add the round-trip-time columns ---
        if (hop != last_hop):

            # --- CREATE 'new_row' FOR 'route_hops' ---
            new_row = list(orig_row)
            route_hops.append(new_row)

            for n in range(number_of_attempts - 1):
                new_row.insert (rttms1_col+1, None)

            last_hop = hop

        # --- Else, add the new round-trip-time value to one of the new columns ---
        else:
            attempt = orig_row[attempt_col]
            new_row[rttms1_col + (attempt-1)] = orig_row[rttms1_col]

    return route_hops

def html_submitter_table (field_names, result_list, link_to,
                          generic_headers_link_to='',
                          specific_headers_link_to={} ):

    # --- Note: these numbers should be auto generated by this function ---
    country_col = 1
    traceroute_col = 0
    dest_col = 4
    nsa_col = 6
    hotel_col = 7

    itag = 'img width="10" src='
    icons = [0,1,2,3]

    html = xml_utils ( )
    doc = ''

    doc += html.tag ("table")
    doc += html.tag ("tr")

    for field in field_names[:nsa_col]:
        doc += html.tagged_text ("th", field)

    doc += html.end_tag ("/tr")

    result_list = list(result_list)

    # for record_id in range ( len(result_list) ):

    record_id = 0
    while record_id < len(result_list):
        record = result_list[record_id]
        doc += html.tag ("tr")

        # --- Determine which countries this route goes through ---
        is_canada = False
        is_us = False
        traceroute_id = record[traceroute_col]
        counter = 0
        while True:
            if record[country_col] == "CA":
                is_canada = True
            elif record[country_col] == "US":
                is_us = True
            if ( len(result_list) > (record_id+1)
                 and result_list[record_id+1][traceroute_col] == traceroute_id ):
                record_id = record_id + 1
                record = result_list[record_id]
            else:
                break

        # --- Determine whether this route goes through NSA-posts or C-Hotels ---
        is_nsa =   True if (record[nsa_col]=='t')   else False
        is_hotel = True if (record[hotel_col]=='t') else False

        if link_to:
            field0 = record[0]
            link = ("tr-query.cgi?query_type=" + link_to + "&arg="
                    + urllib.quote_plus (str(field0) ) )
            doc += html.tagged_text ("td", 'a href="' + link + '"', field0)

        else:
            doc += html.tagged_text ('td', record[0])

        for item_num in range ( 1, nsa_col ):

            if item_num == country_col:
                doc += html.tag ("td")

                icons[0] = "nsa_class_A"  if is_nsa else "clear"
                icons[1] = "carrierhotel" if is_hotel else "clear"
                icons[2] = "US" if is_us else "clear"
                icons[3] = "CA" if is_canada else "clear"

                for i in range ( len(icons) ):
                    icons[i] = ICON_PREFIX + icons[i] + ICON_SUFFIX

                # doc += html.empty_tag ( itag + icons[0], itag + icons[1],
                        # itag + icons[2], itag + icons[3])

                doc += html.empty_tag ( itag + icons[0])
                doc += html.empty_tag ( itag + icons[1])
                doc += html.empty_tag ( itag + icons[2])
                doc += html.empty_tag ( itag + icons[3])

                doc += html.end_tag ("/td")

            else:
                doc += html.tagged_text ("td", record[item_num])
        doc += html.end_tag ("/tr")

        record_id += 1

    doc += html.end_tag ("/table")

    return doc

def html_traceroute_details_page (query_info, arg=None):  
    route_overview = ixmaps.get_traceroute (conn, int(arg) )

    html = xml_utils ( )
    doc = ''

    if query_info.title:
        doc += html.tagged_text ('h1', query_info.title)

    if query_info.header:
        # doc += html.text (query_info.header % ( (instances_of_strings(query_info.header),) * instances_of_strings (query_info.header) ) )
        doc += html.text (query_info.header %
                          ( (arg, arg, route_overview['zip_code'],
                          route_overview['dest'],
                          route_overview['dest_ip'],
                          route_overview['submitter'],
                          route_overview['sub_time'],
                             ) ) )



    # instances_of_arg = instances_of_strings (query_info.query)
    # query = query_info.query % ((arg, ) * instances_of_arg)

    query = query_info.query % (
        (arg, ) * instances_of_strings (query_info.query) )

    q_result = conn.query (query)

    field_names = q_result.listfields ( )
    result_list = q_result.getresult ( )
    
    if (query_info.custom_table_function):
        doc += html.indent (
            query_info.custom_table_function (
                field_names, result_list, query_info.link_to,
                query_info.generic_headers_link_to,
                query_info.specific_headers_link_to) )

    else:
        doc += html.indent (
            html_generic_query_results_table (
                field_names, result_list, query_info.link_to,
                query_info.generic_headers_link_to,
                query_info.specific_headers_link_to) )

    doc += html.tag ('p')
    doc += html.tagged_text ('b', 'SQL Query')
    doc += html.tag ('ul')

    doc += query

    doc += html.end_tag ('/ul')
    doc += html.end_tag ('/p')

    doc += html.empty_tag ('hr')

    if query_info.footer:
        doc += html.text (query_info.footer % ( (arg,) * instances_of_strings (query_info.footer) ) )

    return doc

def instances_of_strings (string):
    return string.count('%s') - string.count('%%s')

def convert_attempts_to_hops_no_rtt (route_hop_attempts):
    attempt_col = 0
    hop_col = 1

    # --- Note: for this function to work, rttms1_col must be a
    #     greater number than attempt_col and hop_col ---
    rttms1_col = 3

    last_hop = 0
    route_hops = []

    for i in range(len(route_hop_attempts) ):
        orig_row = route_hop_attempts[i]
        hop = orig_row[hop_col]

        # --- If this is a new hop, add the round-trip-time columns ---
        if (hop != last_hop):

            # --- CREATE 'new_row' FOR 'route_hops' ---
            new_row = list(orig_row)
            route_hops.append(new_row)

            last_hop = hop

    return route_hops


def array_2d(rows, cols):
    a=[None]*rows
    for i in range(rows):
        a[i] = [None]*cols
    return a

def get_min_latency(hop, rtt_array, nhop):
    x = 0
    mins_list = []
    hop = int(hop)
    nhop = int(nhop)
    while x < nhop:
        mins_list.append(get_lowest_positive(rtt_array[x]))
        x=x+1
    x = len(mins_list)
    while x > hop:
        if (mins_list[x-2] > mins_list[x-1]) and (mins_list[x-1] != '*'):
            mins_list[x-2] = mins_list[x-1]
        x=x-1
    return mins_list[hop]

def get_lowest_positive(number_list):
    x = sys.maxint;
    for item in number_list:
        if item < x and item > -1:
            x = item
    if x == sys.maxint:
        x = '*'
    return x

def get_geo_precision (certainty, lat, long):
    if certainty != None: certainty = str(certainty)
    if lat != None:       lat = str(lat)
    if long != None:      long = str(long)
    if (type (certainty) is str) and certainty.isdigit():
        lat_digits = len(lat) - lat.find('.') - 1
        long_digits = len(long) - long.find('.') - 1
        if lat_digits >= 5 or long_digits >= 5:
            geo_precision = 'building level'
        elif lat_digits <= 2 or long_digits <= 2:
            geo_precision = 'city level'
        else:
            geo_precision = 'postal code level'         #don't know if this condition will ever occur...
    else:
        geo_precision = 'Maxmind'

    return geo_precision

def get_nsa_flag (ipInfo=None, ip=None, conn=None, long_lat=None):
    if not ixmaps.is_nsa (ipInfo, ip, conn, long_lat):
        return "clear"

    else:
        return ( "nsa_class_" + ixmaps.get_nsa_class (ipInfo, ip, conn, long_lat) )

def html_legend ( ):

    legend_text="""
    <p>
  <table>
    <tr><th colspan="4" align="left">Legend </th></tr> 
    <tr>
      <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
      <td><img width='10' src="%snsa_class_A%s"></td>
      <td>NSA:</td><td>Known NSA listening facility in the city</td></tr>
    <tr>
      <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
      <td><img width='10' src="%snsa_class_B%s"></td>
      <td>NSA:</td><td>Suspected NSA listening facility in the city</td></tr>
    <tr>
      <td>&nbsp;&nbsp;&nbsp;&nbsp;</td>
      <td><img width='10' src="%scarrierhotel%s">&nbsp;</td>
      <td>Hotel:</td><td>Carrier hotel exchange point</td></tr>
  </table>
  <br/><br/><br/>
  </p>
""" % (ICON_PREFIX, ICON_SUFFIX, ICON_PREFIX, ICON_SUFFIX, ICON_PREFIX, ICON_SUFFIX)

    return legend_text
