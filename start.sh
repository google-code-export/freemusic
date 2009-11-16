#!/bin/sh
cd $(dirname $0)
python ../google_appengine/dev_appserver.py -p 8081 ./website
