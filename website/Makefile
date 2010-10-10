all: rebuild

upload: all
	gae-upload

clean:
	rm -f dump bulkloader-* *.pyc

rebuild: static/styles.css

static/styles.css: static/styles/*.css
	cat static/styles/*.css | csstidy - --template=highest --silent=true > static/styles.css
