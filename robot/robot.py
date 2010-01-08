#! /usr/bin/python
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
#   файл transcode.log с журналом выполненных действий и album.xml,
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

import getopt, sys, os
import urllib, urllib2, urlparse
import base64, hmac, hashlib
import subprocess
import traceback
import tempfile
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

# local imports
from transcoder import Transcoder

try:
	import yaml
except:
	print "Please install python-yaml."
	sys.exit(1)

class Robot:
	def __init__(self, opts):
		self.verbose = False
		self.force = False
		self.password = ''
		self.host = None
		self.owner = None
		self.debug = False
		self.upload_dir = None
		self.upload_base_url = None

		config = yaml.load(self.read_file('$HOME/.config/freemusic.yaml', 'utf-8'))
		if config:
			for k in config.keys():
				if hasattr(self, k):
					setattr(self, k, config[k])

	def uploadAlbum(self, xml):
		try:
			parseString(xml)
		except ExpatError, e:
			print "Invalid XML file:", e
			sys.exit(1)

		data = { 'xml': xml, 'signature': self.sign(xml) }
		if self.force:
			data['replace'] = 1
		self.post('upload/api', data)

	def post(self, url, data):
		if not self.host:
			raise Exception('host not set')
		url = 'http://' + self.host + '/' + url
		try:
			body = urllib.urlencode(data)
			if self.verbose:
				print "> uploading to %s: %s." % (url, body)
			req = urllib2.Request(url, body)
			response = urllib2.urlopen(req)
			self.showResponse(response.read())
		except urllib2.HTTPError, e:
			print str(e)

	def showResponse(self, response):
		xml = parseString(response)
		for em in xml.getElementsByTagName("response"):
			message = unicode(em.attributes["status"].value)
			if message == u"ok":
				message = u""
			try:
				extra = unicode(em.attributes["message"].value)
				if message:
					message += u": "
				message += extra
			except KeyError:
				pass
			print message
			return
		raise Exception("FAIL")

	def sign(self, data):
		dm = hmac.new(self.password, data, hashlib.sha1)
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
		except urllib2.HTTPError, e:
			print "Error: " + str(e)

	def processZipFile(self, filename, realname=None, owner=None):
		if realname is None:
			realname = os.path.split(filename)[1]
		url = Transcoder(upload_dir=self.upload_dir, owner=owner).transcode(filename, realname)
		if url and self.upload_base_url:
			url = self.upload_base_url + url
		if url:
			self.submit_url(url)

	def processQueue(self):
		if not self.host:
			raise Exception(u'Host name not set, either use -h or ~/.config/freemusic.yaml')
		if not self.upload_dir:
			raise Exception(u'upload_dir not set in ~/.config/freemusic.yaml')

		items = yaml.load(self.fetch('http://' + self.host + '/api/queue.yaml'))
		if items is None:
			print "Nothing to do."
			return

		for item in items:
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
		url = self.get_api_url('api/submit/album', {
			'url': url,
			'signature': self.sign(url),
		})
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
		url = 'http://' + self.host + '/' + path
		if args:
			url += '?' + urllib.urlencode(args)
		return url

def usage():
	print "Usage: %s [options]" % (os.path.basename(sys.argv[0]))
	print "\nBasic options:"
	print " -a filename.xml  upload an album from this file"
	print " -f               force (overwrite existing albums, etc)"
	print " -h host          host name"
	print " -q               process all incoming files"
	print " -s url           submit album.xml"
	print " -u filename      process and upload a single zip file"
	print " -v               be verbose"
	return 2

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "a:dfh:p:qs:u:v")
	except getopt.GetoptError, err:
		return usage()

	if not len(opts):
		return usage()

	r = Robot(opts)
	for option, value in opts:
		if option in ('-u', '-q'):
			print "Working with " + r.host
		if '-a' == option:
			f = open(value, 'r')
			r.uploadAlbum(f.read())
			f.close()
		if '-f' == option:
			r.force = True
		if '-h' == option:
			r.host = value
		if '-v' == option:
			r.verbose = True
		if '-p' == option:
			r.password = value
		if '-q' == option:
			r.processQueue()
		if '-s' == option:
			r.submit_url(value)
		if '-u' == option:
			r.processZipFile(value)

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
	sys.exit(1)
