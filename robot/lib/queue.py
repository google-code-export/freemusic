# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import os
import traceback

from myxml import fetchxml
from settings import settings
from transcoder import Transcoder
from util import download, fetch, mail, sign, upload

def get():
	result = []
	print 'Checking queue at', settings['host']
	xml = fetchxml('http://' + settings['host'] + '/upload/queue')
	if 'moderator' in xml.find('/queue').attrib:
		moderator = str(xml.find('/queue').attrib['moderator'])
		print 'Queue moderator is', moderator
	else:
		moderator = None
	for file in xml.findall('/queue/S3File'):
		result.append({
			'id': int(file.attrib['id']),
			'owner': unicode(file.attrib['owner']),
			'uri': str(file.attrib['file-uri']),
			'moderator': moderator
		})
	return result

def submit(id, url):
	"""
	Отправляет на сервер ссылку на готовый album.xml. Ссылка должна быть
	доступна извне, сервер будет её запрашивать.
	"""
	print "Submitting item %u (%s)" % (id, url)
	fetch('http://' + settings['host'] + '/upload/queue', {
		'id': id,
		'url': url,
		'signature': sign(url),
	})

def process():
	for item in get():
		try:
			item['uri'] = 'http://home.umonkey.net/public/Biopsyhoz_Dihanie_part1_2007.zip'
			zipname = download(item['uri'])
			try:
				lpath = processZipFile(zipname, realname=item['uri'].split('/')[-1], owner=item['owner'])
				print 'GOT:', lpath
				if lpath is not None:
					upload(lpath)
					submit(item['id'], settings['s3base'] + os.path.split(lpath)[-1] + '/album.xml')
				os.remove(zipname)
			except:
				os.remove(zipname)
				raise
		except Exception, e:
			print "    ERROR: " + str(e)
			traceback.print_exc()

def processZipFile(filename, realname=None, owner=None):
	"""
	Возвращает путь к папке с обработанными файлами.
	"""
	if realname is None:
		realname = os.path.split(filename)[1]
	return Transcoder(owner=owner).transcode(filename, realname)
