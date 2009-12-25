#!/bin/sh
cd $(dirname $0)
rm -f artist-*.xml
wget -qO import.xml 'http://ebm.net.ru/api/node/list.xml?class=release,file,artist&limit=none' \
  && xsltproc import.xsl import.xml > data.xml
for f in album-*.xml; do
  echo "Processing $f..."
  ../robot.py -fa $f
done
rm -f album-*.xml
