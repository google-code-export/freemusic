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
		self.queue = None

		config = yaml.load(self.readFile('$HOME/.config/freemusic.yaml'))
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

	def readFile(self, filename):
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
		return data

	def fetch(self, url, data=None):
		"""
		Запрашивает указанный URL, возвращает результат.  Если указан параметр data,
		его содержимое отправляется методом POST (обычно это словарь).
		"""
		if data is not None:
			data = urllib.urlencode(data)
		return urllib2.urlopen(urllib2.Request(url.encode('utf-8'), data)).read()

	def fetch_file(self, url):
		filename = tempfile.mkstemp(suffix='.zip', prefix='freemusic-')[1]
		print "  fetching %s\n    as %s" % (url, filename)
		open(filename, 'wb').write(self.fetch(url))
		return filename

	def processZipFile(self, filename, owner=None):
		Transcoder(upload_dir=self.upload_dir, owner=owner).transcode(filename)

	def processQueue(self):
		if not self.queue:
			raise Exception(u'Queue URL must be set in the config (key "queue").')

		for item in yaml.load(self.fetch(self.queue)):
			print "Item #%u from %s" % (item['id'], item['owner'])
			try:
				zipname = self.fetch_file(item['uri'])
				self.processZipFile(zipname, item['owner'])
				os.remove(zipname)
				self.dequeue(item['id'])
			except Exception, e:
				print "    ERROR: " + str(e)

	def dequeue(self, id):
		parts = urlparse.urlparse(self.queue)
		url = parts[0] + '://' + parts[1] + '/api/queue/delete?id=' + str(id) + '&signature=' + urllib.quote(self.sign(str(id)))
		print "  dequeueing"
		print "    " + url
		self.fetch(url)

def usage():
	print "Usage: %s [options]" % (os.path.basename(sys.argv[0]))
	print "\nBasic options:"
	print " -a filename.xml  upload an album from this file"
	print " -f               force (overwrite existing albums, etc)"
	print " -h host          host name"
	print " -q               process all incoming files"
	print " -u filename      process and upload a single zip file"
	print " -v               be verbose"
	return 2

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "a:dfh:p:qu:v")
	except getopt.GetoptError, err:
		return usage()

	if not len(opts):
		return usage()

	r = Robot(opts)
	for option, value in opts:
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
		if '-u' == option:
			r.processZipFile(value)

if __name__ == '__main__':
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		print "\rInterrupted."
	except Exception, e:
		print "\r%s: %s" % (e.__class__.__name__, str(e))
		traceback.print_exc()
	sys.exit(1)
