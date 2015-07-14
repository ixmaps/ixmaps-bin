#!/bin/bash

# remove stale lock files

lock_file_dir=/var/run/ixmaps

find $lock_file_dir -name \*.lock -mtime +1 -delete
     
