all: rebuild

upload: all
	hg push
	gae-upload

clean:
	rm -f dump bulkloader-* *.pyc

rebuild: static/styles.css static/scripts.js

static/styles.css: static/styles/*.css
	cat static/styles/*.css | csstidy - --template=highest --silent=true > static/styles.css

static/scripts.js: static/scripts/*.js
	cat static/scripts/*.js > static/scripts.js
