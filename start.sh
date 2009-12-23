#!/bin/sh
cd $(dirname $0)/website
python ../../google_appengine/dev_appserver.py \
  -p 8081 \
  --blobstore_path=../tmp/blobstore \
  --datastore_path=../tmp/datastore \
  --history_path=../tmp/datastore.history \
  --require_indexes \
  .
