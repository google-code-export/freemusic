# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"Всё, что касается работы с метками."

__author__ = 'justin.forest@gmail.com'

from logging import debug as log

from google.appengine.ext import db
from google.appengine.api import memcache

import base
import model
import myxml

class LabelStats(db.Model):
	xml = db.TextProperty()

class List(base.BaseRequestHandler):
	xsltName = 'labels.xsl'

	def get(self):
		stats = LabelStats.all().get()
		if stats is not None:
			self.sendXML(stats.xml)
		else:
			self.sendXML(u'<labels/>')

class Cache(base.BaseRequestHandler):
	def post(self):
		if 'X-AppEngine-QueueName' not in self.request.headers:
			raise Exception('Task Queue only.')
		saved = LabelStats.all().get()
		if saved is None:
			saved = LabelStats()
		result = {}
		for album in model.SiteAlbum.all().fetch(1000):
			if album.labels:
				for label in album.labels:
					if label not in result:
						result[label] = 1
					else:
						result[label] += 1
		saved.xml = myxml.em(u'labels', content=u''.join([myxml.em(u'label', {'weight': result[k], 'uri': myxml.uri(k)}, k) for k in sorted(result)]))
		saved.put()

if __name__ == '__main__':
	base.run([
		('/labels', List),
		('/labels/cache', Cache),
	])
