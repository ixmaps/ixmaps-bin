## A set of backend scripts required to keep everything afloat

#### Server setup requires cloning these into the /home/ixmaps/bin directory (and setting up the requisite cronjobs)

download_maxmind.py
```
location: /home/ixmaps/bin/download_maxmind.sh
purpose: update our Maxmind data store
invocation: cronjob once per month 0 2 15 * * /home/ixmaps/bin/download_maxmind.sh
```

corr-latlong.sh
```
location: /home/ixmaps/bin/corr-latlong.sh
purpose: update the lat and long of newly added routes using IXmaps rules
invocation:
-N flag by cronjob every time minutes   */10 * * * * /home/ixmaps/bin/corr-latlong.sh -u
-U flag by cronjob once per day   0 5 * * * /home/ixmaps/bin/corr-latlong.sh -u
input flag: p_status = 'N' or p_status = 'G' or p_status = 'U'
output flag: p_status of 'U' -> p_status of 'N'
```

create-extra-db-tables.sh
```
location: /home/ixmaps/bin/create-extra-db-tables.sh
purpose: create/update the convenience tables in the DB
invocation: cronjob once per day   0 6 * * * /home/ixmaps/bin/create-extra-db-tables.sh
```

verify_trsets.py
```
location: /home/ixmaps/bin/verify_trsets.py
purpose: flag trset urls that are no longer reaching their target
invocation: cronjob once per day   30 4 * * * python /home/ixmaps/bin/verify_trsets.py
```

## License
Copyright (C) 2020 IXmaps.
These scripts [github.com/ixmaps/ixmaps-bin](https://github.com/ixmaps/ixmaps-bin) are licensed under a GNU AGPL v3.0 license. All files are free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3 of the License.

These scripts are distributed in the hope that they will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details [gnu.org/licenses](https://gnu.org/licenses/agpl.html).