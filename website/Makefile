all:
	@echo "Targets: copydata dump clean."

copydata: dump
	bulkloader.py --email=${MAIL} --restore --app_id=free-music --url=http://127.0.0.1:8080/remote_api --filename=dump

dump:
	bulkloader.py --email=${MAIL} --dump --app_id=free-music --url=http://free-music.appspot.com/remote_api --filename=dump

clean:
	rm -f dump bulkloader-* *.pyc
