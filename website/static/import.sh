#!/bin/sh
wget -qO import.xml 'http://ebm.net.ru/api/node/list.xml?class=release,file,artist&limit=none' \
  && xsltproc import.xsl import.xml > data.xml
