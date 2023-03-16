#!/bin/bash

mkdir -p data/raw/ecoregions

curl -o tmp/official_teow.zip https://files.worldwildlife.org/wwfcmsprod/files/Publication/file/6kcchn7e3u_official_teow.zip?_ga=2.252261194.2115546270.1678845839-789025250.1678845839
unzip tmp/official_teow.zip -d data/raw/ecoregions
rm -f tmp/official_teow.zip
