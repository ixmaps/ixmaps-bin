## A set of backend scripts required to keep everything afloat

### Server setup requires cloning these into the /home/ixmaps/bin directory (and setting up the requisite cronjobs)

**download_maxmind.py**
```
location: /home/ixmaps/bin/download_maxmind.py
purpose: update our Maxmind data store
invocation: cronjob once per month 0 2 15 * * /home/ixmaps/bin/download_maxmind.py
```

**corr-latlong.sh**
```
location: /home/ixmaps/bin/corr-latlong.sh
purpose: update the lat and long of newly added routes using IXmaps rules
invocation:
-N flag by cronjob every time minutes   */10 * * * * /home/ixmaps/bin/corr-latlong.sh -u
-U flag by cronjob once per day   0 5 * * * /home/ixmaps/bin/corr-latlong.sh -u
input flag: p_status = 'N' or p_status = 'G' or p_status = 'U'
output flag: p_status of 'U' -> p_status of 'N'
```

**create-extra-db-tables.sh**
```
location: /home/ixmaps/bin/create-extra-db-tables.sh
purpose: create/update the convenience tables in the DB
invocation: cronjob once per day   0 6 * * * /home/ixmaps/bin/create-extra-db-tables.sh
```

**concat-trsets.sh**
```
location: /home/ixmaps/bin/concat-trsets.sh
purpose: concatenate all of the trsets into one giant trset (for use with the IXmapsClient)
invocation: cronjob once per day   30 5 * * * /home/ixmaps/bin/concat-trsets.sh
```
