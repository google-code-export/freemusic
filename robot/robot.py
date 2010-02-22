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

import base64
import getopt
import hmac
import hashlib
import os
import subprocess
import sys
import tempfile
import time
import traceback
import urllib
import urllib2
import urlparse
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

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

class Robot:
	def sign(self, data):
		dm = hmac.new(settings['password'], data, hashlib.sha1)
		return base64.b64encode(dm.digest())

	def read_file(self, filename, encoding=None):
		"""
		Возвращает содержимое указанного файла.  Если файла нет, возвращает пустую строку.
		"""
		filename = os.path.expandvars(filename)
		if os.path.exists(filename):
			f = open(filename, "r")
			data = f.read()
		else:
			print "no file: ", filename
			data = ""
		if encoding is not None:
			data = data.decode(encoding)
		return data

	def fetch(self, url, data=None):
		"""
		Запрашивает указанный URL, возвращает результат.  Если указан параметр data,
		его содержимое отправляется методом POST (обычно это словарь).
		"""
		try:
			if data is not None:
				data = urllib.urlencode(data)
			return urllib2.urlopen(urllib2.Request(url.encode('utf-8'), data)).read()
		except urllib2.HTTPError, e:
			print "Error fetching %s: %s" % (url, e)

	def fetch_file(self, url):
		filename = tempfile.mkstemp(suffix='.zip', prefix='freemusic-')[1]
		print "  fetching %s\n    as %s" % (url, filename)

		try:
			o = open(filename, 'wb')
			try:
				i = urllib2.urlopen(urllib2.Request(url.encode('utf-8')))
				bytes = 0
				while True:
					block = i.read(163840)
					if len(block) == 0:
						break
					o.write(block)
					bytes += len(block)
					print "%fM\r" % (float(bytes) / 1048576),

				# open(filename, 'wb').write(self.fetch(url))
				return filename
			except:
				o.close()
				os.unlink(o.name)
				raise
		except urllib2.HTTPError, e:
			print "Error: " + str(e)

	def processZipFile(self, filename, realname=None, owner=None):
		if realname is None:
			realname = os.path.split(filename)[1]
		url = Transcoder(owner=owner).transcode(filename, realname)
		if url and settings['upload_base_url']:
			url = settings['upload_base_url'] + url
		if url:
			self.submit_url(url)

	def processQueue(self):
		items = yaml.load(self.fetch('http://' + settings['host'] + '/api/queue.yaml'))
		if items is None:
			if settings['verbose']:
				print "Nothing to do."
			return

		skip = settings['skip']

		for item in items:
			if item['uri'] not in skip:
				print "A file from " + item['owner']
				try:
					zipname = self.fetch_file(item['uri'])
					if zipname:
						try:
							self.processZipFile(zipname, realname=item['uri'].split('/')[-1], owner=item['owner'])
							os.remove(zipname)
							self.dequeue(item['uri'])
						except:
							os.remove(zipname)
							raise
				except Exception, e:
					print "    ERROR: " + str(e)
					traceback.print_exc()

	def submit_url(self, url):
		"""
		Просит сервер добавить альбом, информация о котором находится по указанному адресу.
		"""
		data = {
			'url': url,
			'signature': self.sign(url),
			'replace': settings['force'],
		}
		if settings['force']:
			data['replace'] = 1
		url = self.get_api_url('api/submit/album', data)
		self.fetch(url)

	def dequeue(self, url):
		url = self.get_api_url('api/queue/delete', {
			'url': url,
			'signature': self.sign(url),
		})
		print "  dequeueing"
		print "    " + url
		self.fetch(url)

	def get_api_url(self, path, args=None):
		url = 'http://' + settings['host'] + '/' + path
		if args:
			url += '?' + urllib.urlencode(args)
		return url

def usage():
	print "Usage: %s [options]" % (os.path.basename(sys.argv[0]))
	print "\nBasic options:"
	print " -d key=value        override config options"
	print " -f                  force (overwrite existing albums, etc)"
	print " -h host             host name"
	print " -j                  run the Jabber bot"
	print " -q                  process all incoming files"
	print " -s urls...          submit one or more album.xml"
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
		opts, args = getopt.getopt(sys.argv[1:], "a:d:fh:jp:qsu:wv")
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

	r = Robot()
	for option, value in opts:
		if option in ('-u', '-q', '-w'):
			print "Working with " + settings['host']
		if '-j' == option:
			lib.jabberbot.run(settings)
		if '-v' == option:
			r.verbose = True
		if '-p' == option:
			r.password = value
		if '-q' == option:
			r.processQueue()
		if '-s' == option:
			if not len(args):
				usage()
			for url in args:
				r.submit_url(url)
		if '-u' == option:
			r.processZipFile(value)
		if '-w' == option:
			while True:
				r.processQueue()
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
