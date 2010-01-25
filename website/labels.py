# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"Всё, что касается работы с метками."

__author__ = 'justin.forest@gmail.com'

from base import BaseRequestHandler
from model import SiteAlbum
import myxml

class List(BaseRequestHandler):
	pageName = 'labels'

	def get(self):
		result = {}
		for album in SiteAlbum.all().fetch(1000):
			if album.labels:
				for label in album.labels:
					if label not in result:
						result[label] = 1
					else:
						result[label] += 1

		xml = u''
		for k in result:
			xml += myxml.em(u'label', {
				'weight': result[k],
				'uri': myxml.uri(k),
				}, content=k)

		self.sendXML(myxml.em(u'labels', content=xml))
