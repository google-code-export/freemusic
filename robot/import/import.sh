#!/bin/sh
set -u
cd $(dirname $0)
rm -f artist-*.xml
trap "rm -f *.xml; exit 1" INT
echo "Downloading from ebm.net.ru..."
wget -qO import.xml 'http://ebm.net.ru/api/node/list.xml?class=release,file,artist&limit=none' \
  && xsltproc import.xsl import.xml > data.xml
echo "Uploading to AppEngine..."
for f in album-*.xml; do
  ../robot.py -fa $f
done
rm -f album-*.xml
