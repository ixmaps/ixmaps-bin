#!/usr/bin/python

import sys
import ixmaps
from ixmaps import MutexFile

# def get_traceroute_differences(conn):

#     # --- ('conn' is only needed here because we only query once) ---

#     if not conn:
#         conn = ixmaps.getConnection()
    

def find_new_traceroutes (conn=None):
    if not conn:
        conn = ixmaps.DBConnect.getConnection()

    sql = """select id from traceroute where id not in (
    select traceroute.id from traceroute, traceroute_traits 
    where traceroute.id = traceroute_traits.id)
order by id"""

    qres = conn.query (sql)
    return qres

def find_unknown_traceroutes (conn=None):
    if not conn:
        conn = ixmaps.DBConnect.getConnection()

    sql = """(
    select id from traceroute_traits where id not in (
        select traceroute.id from traceroute, traceroute_traits
        where traceroute.id = traceroute_traits.id)
)
union
(
    select traceroute_id from traceroute_countries where traceroute_id not in 
    (
        select traceroute.id from traceroute, traceroute_countries
        where traceroute.id = traceroute_countries.traceroute_id
    )
)
order by 1"""

    qres = conn.query (sql)
    return qres

def find_all_traceroutes (conn=None):
    if not conn:
        conn = ixmaps.DBConnect.getConnection()

    qres = conn.query ("select id from traceroute order by id")
    return qres

def get_tr_items_dim(da):
    """da is array of dicts, each dict representing a single traceroute probe"""
    nhops = nattempts = 0
    for d in da:
        if d['attempt'] > nattempts:
            nattempts = d['attempt']
        if d['hop'] > nhops:
            nhops = d['hop']
    return (nhops, nattempts)

def add_traceroutes (conn, new_traceroutes_db, be_verbose=False):
    lock=MutexFile(LOCK_FILE)
    if not lock.acquire ():
        return False

    if not conn:
        conn = ixmaps.DBConnect.getConnection()
    
    new_traceroutes = new_traceroutes_db.dictresult()

    insert_into_traits = ""
    insert_into_countries = ""

    for traceroute in new_traceroutes:

        traceroute_id = traceroute['id']

        if be_verbose:
            print traceroute_id

        qres = conn.query ("select * from tr_item where traceroute_id=%i" 
                            % traceroute_id)

        tr_body = qres.dictresult()

        if not tr_body: continue

        (nhops, nattempts) = get_tr_items_dim (tr_body)

        ipaddrs = [None] * nhops
        # ip_info = [None] * nhops

        # print "tr_body:" , tr_body

        for probe in tr_body:
            # print "    probe['hop']:", probe['hop']
            hop = probe['hop']-1

            # --- There are multiple attempts for each hop, but we
            #     only need one, so, after you aquire an IP, ignore
            #     further attempts ---
            if (ipaddrs[hop]):
                continue     
            ipaddrs[hop] = probe['ip_addr']

        # for hop in range (nhops):
            # ip_info[hop] = ixmaps.get_ip_addr_info (ipaddrs[hop], conn)

        ip_info = get_ip_addr_info_list (ipaddrs, conn)

        number_of_ips = len(ip_info)

        is_nsa = False
        # print "ip_info:", ip_info
        # print "len(ip_info):", len (ip_info)
        # print "len(ipaddrs):", len(ipaddrs)
        # print "ipaddrs:", ipaddrs
        # print "number_of_ips:", number_of_ips

        # print "for hop in range (number_of_ips):"
        for hop in range (number_of_ips):
            # print '    ipaddrs[' + str(hop) + ']:', ipaddrs[hop]
            pr_addr = ipaddrs[hop]
            # print (ip_info[hop])
            is_nsa = ixmaps.is_nsa(ip_info[hop])
            # print "    is_nsa:", is_nsa
            if is_nsa == True:
                break

        is_chotel = False
        # print "for hop in range (number_of_ips):"
        for hop in range (number_of_ips):
            pr_addr = ipaddrs[hop]
            # print "    ip_info[" + str(hop) + "]: ", ip_info[hop]
            is_chotel = ixmaps.is_chotel(ip_info[hop])
            if is_chotel == True:
                break

        canada_flag = False
        us_flag = False
        for hop in range (number_of_ips):
            pr_addr = ipaddrs[hop]
            country = ixmaps.get_country (ip_info[hop])
            if country == "CA":
                canada_flag = True
            if country == "US":
                us_flag = True
            if (canada_flag == True) and (us_flag == True):
                break

        # --- Remove, so as not to get an SQL error, just in case some
        #     traits-data for this traceroute already exists ---
        conn.query ("delete from traceroute_traits where id = %i" % traceroute_id)
        conn.query ("""insert into traceroute_traits (id, nsa, hotel)
        values (%i, %s, %s)""" % (traceroute_id, is_nsa, is_chotel))

        # --- Remove, so as not to get an SQL error, just in case some
        #     country-data for this traceroute already exists ---
        if canada_flag or us_flag:
            conn.query("delete from traceroute_countries where traceroute_id = %s" \
                       % (traceroute_id) )

            if canada_flag:
                conn.query ("""insert into traceroute_countries (country_code, traceroute_id)
                values ('CA', %i)""" % traceroute_id)
            if us_flag:
                conn.query ("""insert into traceroute_countries (country_code, traceroute_id)
                values ('US', %i)""" % traceroute_id)

    return True

def purge_unknown_traceroutes (conn, unknown_traceroutes_db):
    lock=MutexFile(LOCK_FILE)
    if not lock.acquire ():
        return False

    if not conn:
        conn = ixmaps.DBConnect.getConnection()

    unknown_traceroutes = unknown_traceroutes_db.dictresult()
    if len(unknown_traceroutes) == 0:
        return

    ids_to_purge = ""
    was_previous_traceroute = False
    for traceroute in unknown_traceroutes:
        if was_previous_traceroute:
            ids_to_purge += ", "
        else:
            was_previous_traceroute = True

        ids_to_purge += str(traceroute['id'])

    qstr = "delete from traceroute_traits where id in (%s)" % (ids_to_purge)
    # print qstr
    conn.query (qstr)

    qstr = "delete from traceroute_countries where traceroute_id in (%s)" \
           % (ids_to_purge)
    # print qstr
    conn.query (qstr)

    return True

def drop_tables (conn):
    conn.query ("drop table traceroute_traits;")
    conn.query ("drop table traceroute_countries;")
    # conn.query ("drop table countries;")

def build_tables(conn):
    lock=MutexFile(LOCK_FILE)
    if not lock.acquire ():
        return False

    if not conn:
        conn = ixmaps.DBConnect.getConnection()

    # --- Create traceroute_traits table ---
    conn.query ("""
    --
    -- Name: traceroute_traits; Type: TABLE; Schema: public; Owner: ixmaps; Tablespace: 
    --
    
    CREATE TABLE traceroute_traits (
        id integer PRIMARY KEY,
        nsa boolean,
        hotel boolean
    );
    
    
    ALTER TABLE public.traceroute_traits OWNER TO ixmaps;
    
    
    
    --
    -- Name: traceroute_traits; Type: ACL; Schema: public; Owner: ixmaps
    --
    
    REVOKE ALL ON TABLE traceroute_traits FROM PUBLIC;
    REVOKE ALL ON TABLE traceroute_traits FROM ixmaps;
    GRANT ALL ON TABLE traceroute_traits TO ixmaps;
    GRANT SELECT ON TABLE traceroute_traits TO PUBLIC;
    """)


    # --- Create traceroute_countries table ---
    conn.query ("""
    --
    -- Name: traceroute_countries; Type: TABLE; Schema: public; Owner: ixmaps; Tablespace: 
    --
    
    CREATE TABLE traceroute_countries (
        country_code character(2) NOT NULL,
        traceroute_id integer NOT NULL,
        PRIMARY KEY (country_code, traceroute_id)
    );
    
    
    ALTER TABLE public.traceroute_countries OWNER TO ixmaps;
    
    --
    -- Name: traceroute_countries; Type: ACL; Schema: public; Owner: ixmaps
    --
    
    REVOKE ALL ON TABLE traceroute_countries FROM PUBLIC;
    REVOKE ALL ON TABLE traceroute_countries FROM ixmaps;
    GRANT ALL ON TABLE traceroute_countries TO ixmaps;
    GRANT SELECT ON TABLE traceroute_countries TO PUBLIC;
    """)


    # # --- Create countries table ---
    # conn.query = ("""
    # --
    # -- Name: country; Type: TABLE; Schema: public; Owner: ixmaps; Tablespace: 
    # --
    
    # CREATE TABLE country (
        # code character(2) NOT NULL,
        # name character varying(27)
    # );
    
    
    # ALTER TABLE public.country OWNER TO ixmaps;
    
    # --
    # -- Data for Name: country; Type: TABLE DATA; Schema: public; Owner: ixmaps
    # --
    
    # COPY country (code, name) FROM stdin;
    # CA	Canada
    # US	United States
    # xx	Unknown
    # \.
    # """)

    return True

def get_ip_addr_info_list(address_list, conn=None):
    if not conn:
        conn = ixmaps.DBConnect.getConnection()

    if address_list:

        # --- Generate SQL query ---
        addresses_str = ''
        for address in address_list:
            if address != None:
                if addresses_str != "":
                    addresses_str += ", "
                addresses_str += "'%s'" % (address)
        # print "addresses_str:", addresses_str

        if addresses_str:
            qres = conn.query("select * from ip_addr_info where ip_addr in (%s)"
                              % addresses_str)
        else:
            qres = None
            return []

        # if len(qres.dictresult()) > 0:

        l = len(qres.dictresult())
        ip_info_list = [None] * l
        for aa in range (0, l):

            d = qres.dictresult()[aa]
            ip_info_list[aa] = {}
            ip_info_list[aa]['lat'] = str(d['lat'])
            ip_info_list[aa]['long'] = str(d['long'])
            ip_info_list[aa]['asnum'] = str(d['asnum'])
            ip_info_list[aa]['country'] = str(d['mm_country'])
            ip_info_list[aa]['region'] = str(d['mm_region'])
            ip_info_list[aa]['city'] = str(d['mm_city'])
            ip_info_list[aa]['pcode'] = str(d['mm_postal'])
            ip_info_list[aa]['area_code'] = str(d['mm_area_code'])
            ip_info_list[aa]['dma_code'] = str(d['mm_dma_code'])
            ip_info_list[aa]['ip_addr'] = d['ip_addr']
            ip_info_list[aa]['hostname'] = d['hostname']
#            ip_info_list[aa]['type'] = d['type']

    if (not address_list) or (len(qres.dictresult())==0):
        ip_info_list=[{'lat': '', 'hostname': '', 'ip_addr': None, 'long': '',
           'asnum': '', 'region': '', 'city': '', 'country': '',
           'pcode': '', 'area_code': '', 'dma_code': ''}]
    return ip_info_list

if __name__ == '__main__':
    import getopt

    LOCK_FILE="save_traceroute_info.lock"

    def help():

        print """
save_traceroute_info.py
=======================

Synopsis: Update the traceroutes traits tables (ie traceroute_traits
          and traceroute_countries) in IXmaps.

Use: save_traceroute_info [options]

Options:
    -A   Add:     Add new traceroutes to the traceroutes traits tables.
    -C   Create:  Create traceroute-traits tables.
    -D   Drop:    Drop (delete) traceroute-traits tables.
    -i   Info:    Display IDs of new traceroutes in the traceroutes table,
                  and unknown traceroute IDs in the TR traits tables.
    -P   Purge:   Purge unknown traceroutes in the traceroute traits tables.
    -R   Rebuild: Rebuild traceroute traits tables, correcting any
                  inconsistencies which may have occurred.  (Processor
                  intensive.)
    -s   Sync:    Add new and Purge unknown traceroutes in TR traits tables.
                  (same as -PA).
    -V   Verbose: Be verbose.
    -h   Help:    Display this help and exit.

Examples:

To create and populate traceroute-traits tables:
   save_traceroute_info -CsV

Useful as a cron to keep traceroute traits tables up to date:
   save_traceroute_info -s
    """ 

    progname = sys.argv[0]


    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "ABCDhiPRsV")
    except getopt.GetoptError, exc:
        print >>sys.stderr, "%s: %s" % (progname, str(exc))
        sys.exit(1)

    if len (opts) == 0:
        help ()
        sys.exit(0)

    show_traceroutes = False
    be_verbose = False
    do_build_tables = False
    do_get_traceroutes = False
    do_get_all_traceroutes = False
    do_get_unknown_traceroutes = False
    do_add_traceroutes = False
    do_add_all_traceroutes = False
    do_purge_traceroutes = False
    do_drop_tables = False

    for flag, value in opts:
        if flag == '-h':
            help ()
            exit (0)

        if flag == '-A':
            do_get_traceroutes = True
            do_add_traceroutes =True

        if flag == '-C':
            do_build_tables = True

        if flag == '-D':
            do_drop_tables = True

        if flag == '-i':
            do_get_traceroutes = True
            do_get_unknown_traceroutes = True
            show_traceroutes = True

        if flag == '-P':
            do_get_unknown_traceroutes = True
            do_purge_traceroutes = True

        if flag == '-R':
            do_get_all_traceroutes = True
            do_get_unknown_traceroutes = True
            do_purge_traceroutes = True
            do_add_all_traceroutes = True

        if flag == '-s':
            do_get_traceroutes = True
            do_get_unknown_traceroutes = False
            do_purge_traceroutes = True
            do_add_traceroutes =True

        if flag == '-V':
            be_verbose = True

conn = ixmaps.DBConnect.getConnection()

# --- Drop Traceroute traits tables ---
if do_drop_tables:
    drop_tables (conn)
    if be_verbose:
        print "do_drop_tables"

# --- Build tables ---
if do_build_tables:
    if be_verbose:
        print "beginning do_build_tables"
    build_tables(conn)
    if be_verbose:
        print "completed do_build_tables"

# --- Find new traceroutes ---
if do_get_traceroutes:
    if be_verbose:
        print "beginning do_get_traceroutes"
    tr = find_new_traceroutes(conn)
    if be_verbose:
        print "completed do_get_traceroutes"

# --- Find unknown traceroutes ---
if do_get_unknown_traceroutes:
    if be_verbose:
        print "beginning do_get_unknown_traceroutes"
    unknown_tr = find_unknown_traceroutes(conn)
    if be_verbose:
        print "completed do_get_unknown_traceroutes"

# --- Get all traceroutes in the traceroute table ---
if do_get_all_traceroutes:
    if be_verbose:
        print "beginning do_get_all_traceroutes"
    all_tr = find_all_traceroutes(conn)
    if be_verbose:
        print "completed do_get_all_traceroutes"

# --- Show new and unknown traceroutes ---
if show_traceroutes:
    print
    print "New traceroutes"
    print "==============="
    print tr
    print "Unknown traceroutes"
    print "==================="
    print unknown_tr
    
# --- Purge unknown traceroutes ---
if do_purge_traceroutes:
    purge_unknown_traceroutes (conn, unknown_tr)

# --- Add new traceroutes ---
if do_add_traceroutes:
    # get_info_on_traceroutes (new_traceroutes)
    add_traceroutes (conn, tr, be_verbose)

# --- Rebuild all traceroutes ---
if do_add_all_traceroutes:
    add_traceroutes (conn, all_tr, be_verbose=be_verbose)
    
