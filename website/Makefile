all: rebuild

upload: clean all
	cat ../.hg/gaepass | appcfg.py -e "$(MAIL)" --passin update .

clean:
	find . -iregex '.*\.\(pyc\|orig\|rej\)$$' -delete

rebuild: static/styles.css static/scripts.js

static/styles.css: static/styles/*.css
	cat static/styles/*.css | csstidy - --template=highest --silent=true > static/styles.css

static/scripts.js: static/scripts/*.js
	cat static/scripts/*.js > static/scripts.js

serve: .tmp/blobstore
	dev_appserver.py --enable_sendmail --use_sqlite --blobstore_path=.tmp/blobstore --datastore_path=.tmp/datastore .

.tmp/blobstore:
	mkdir -p .tmp/blobstore
