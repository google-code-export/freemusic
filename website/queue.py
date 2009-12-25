# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:
#
# Очередь обработки запросов.

from xml.sax.saxutils import escape

from s3 import S3File
from base import BaseRequestHandler

class QueueHandler(BaseRequestHandler):
	def get(self):
		xml = u'<queue>'
		for file in S3File.all().fetch(1000):
			uri = 'http://' + file.bucket + '.s3.amazonaws.com/' + file.path
			xml += u'<file id="%s" name="%s" uri="%s" size="%s" created="%s" owner="%s"/>' % (file.id, file.name, uri, file.size, file.created, file.owner)
		self.sendXML(xml + u'</queue>')
