# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:
#
# Робот, обрабатывающий поступающие от пользователей архивы
# с исходным материалом и формирующий файлы для выгрузки на
# внешний файловый хостинг.
#
# Настройки хранятся в файле ~/.config/freemusic.yaml.
#
# Примеры использования:
#
# ./robot.py -u filename.zip
#
#   Анализирует содержимое указанного архива, кодирует звуковые
#   файлы в нужные форматы, результат работы складывает в папку,
#   указанную в настройках (upload_dir); если папка в настройках
#   не указана, после обработки в папке со временными файлами будет
#   открыт терминал, для анализа полученных файлов (используется
#   для отладки).
#
#   Если архив содержит файлы в форматах сжатия без потерь, они
#   сжимаются в MP3/OGG с высоким качеством (для скачивания),
#   которые затем складываются в архивы -mp3.zip и -ogg.zip (начальная
#   часть имени файла соответствует исходному имени архива).  Также
#   создаются MP3/OGG версии низкого качества для прослушивания
#   на сайте.  Если исходные файлы есть только в ущербном формате,
#   создаются только версии для онлайн-прослушивания, для скачивания
#   будет доступен только один архив с исходными файлами, пережатие
#   не осуществляется.
#
#   В результате работы скрипта в папке upload_dir создаётся папка
#   с уникальным случайным именем, содаржащая все выгружаемые файлы,
#   относящиеся к обработанному альбому.  Это MP3/OGG версии каждой
#   дорожки (для прослушивания через сайт), 1-3 ZIP архива для скачивания,
#   файл transcode-log.txt с журналом выполненных действий и album.xml,
#   содержащий всю информацию об альбоме.
#
#   Предполагается, что все эти файлы загружаются на файловый хостинг,
#   затем веб-серверу отправляется URL файла album.xml, содержащий
#   имена всех остальных файлов (относительные).  Веб-сайт скачивает
#   указанный ему файл album.xml, преобразует содержащиеся в нём ссылки
#   в абсолютные (используя путь к album.xml в качестве основы),
#   и сохраняет информацию в локальном хранилище.  Необходимость
#   скачивания файла album.xml по HTTP гарантирует доступность всех
#   файлов по HTTP (исключается возможность отправить "битую" ссылку).
#
#   Корневой элемент файл album.xml имеет атрибут owner, содержащий
#   email пользователя, загрузившего альбом.  Этот пользователь становится
#   его хозяином после успешной загрузки, ему отправляется уведомление
#   по электронной почте.

import getopt
import os
import sys
import time
import traceback
import urllib2

try:
	import yaml
except:
	print "Please install python-yaml."
	sys.exit(1)

# local imports
from lib import logger
from lib.transcoder import Transcoder
from lib.settings import settings
import lib.jabberbot

from lib import queue
from lib import util

def usage():
	print "Usage: %s [options]" % (os.path.basename(sys.argv[0]))
	print "\nBasic options:"
	print " -d key=value        override config options"
	print " -f                  force (overwrite existing albums, etc)"
	print " -h host             host name"
	print " -j                  run the Jabber bot"
	print " -q                  process all incoming files"
	print " -u filename         process and upload a single zip file"
	print " -w                  work; loops with -q"
	print " -v                  be verbose"
	print "\nConfig options (-d or ~/.config/freemusic.yaml):"
	print "  force              new albums overwrite existing ones"
	print "  host               web site host name"
	print "  password           used for signing, usually equals to S3 private key"
	print "  upload_dir         local path, a folder with dirs and files to upload"
	print "  upload_base_url    public URL by which upload_dir is accessible"
	print "  skip               a list of URLS to ignore if found in queue"
	print "  verbose            send conversion log to stdout, print extra messages"
	return 1

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "a:d:fh:jp:qu:wv")
	except getopt.GetoptError, err:
		return usage()

	if not len(opts):
		return usage()

	# Перегрузка настроек.
	for option, value in opts:
		if '-d' == option:
			k, v = value.split('=', 1)
			settings[k] = v
		if '-f' == option:
			settings['force'] = True
		if '-h' == option:
			settings['host'] = value
		if '-v' == option:
			settings['verbose'] = True

	# Проверка настроек
	settings.validate()

	for option, value in opts:
		if option in ('-u', '-q', '-w'):
			print "Working with " + settings['host']
		if '-j' == option:
			lib.jabberbot.run(settings)
		if '-v' == option:
			r.verbose = True
		if '-q' == option:
			queue.process()
		if '-w' == option:
			while True:
				queue.process()
				time.sleep(60)

if __name__ == '__main__':
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		print "\rInterrupted."
	except Exception, e:
		if isinstance(e, urllib2.URLError):
			print "\r" + str(e)
		else:
			print "\r%s: %s" % (e.__class__.__name__, str(e))
			traceback.print_exc()
	sys.exit(2)
