# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"Всё, что касается работы с метками."

__author__ = 'justin.forest@gmail.com'

from google.appengine.ext import db
from google.appengine.api import memcache

from logging import debug as log
from base import BaseRequestHandler
from model import SiteAlbum
import myxml

class LabelStats(db.Model):
	xml = db.TextProperty()

def load(force_update=False):
	"Загружает метки, поддерживает кэширование. Можно использовать в других модулях."
	cached = memcache.get('/labels')
	if cached is None or force_update:
		saved = LabelStats.all().get()
		if saved is None or force_update:
			if saved is None:
				saved = LabelStats()
			result = {}
			for album in SiteAlbum.all().fetch(1000):
				if album.labels:
					for label in album.labels:
						if label not in result:
							result[label] = 1
						else:
							result[label] += 1
			saved.xml = myxml.em(u'labels', content=u''.join([myxml.em(u'label', {'weight': result[k], 'uri': myxml.uri(k)}, k) for k in result]))
			saved.put()
		cached = saved.xml
	return cached

class List(BaseRequestHandler):
	xsltName = 'labels.xsl'

	def get(self):
		self.sendXML(load(force_update=self.is_cron()))
