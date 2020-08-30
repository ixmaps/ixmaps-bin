#!/bin/bash

# This script concatenates all trsets into one giant trset - now legacy

echo > /srv/www/website/trsets/00:_all_trsets.trset
for filename in /srv/www/website/trsets/*.trset; do
  if [[ "$filename" != "/srv/www/website/trsets/00:_all_trsets.trset" ]]
    then
      cat $filename >> /srv/www/website/trsets/00:_all_trsets.trset
  fi
done
