#!/bin/bash

# This script concatenates all trsets into one giant trset

echo > /var/www/ixmaps/trsets/00:_all_trsets.trset
for filename in /var/www/ixmaps/trsets/*.trset; do
  if [[ "$filename" != "/var/www/ixmaps/trsets/00:_all_trsets.trset" ]]
    then
      cat $filename >> /var/www/ixmaps/trsets/00:_all_trsets.trset
  fi
done
