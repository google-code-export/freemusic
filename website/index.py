# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

# Site imports.
from base import BaseRequestHandler, HTTPException
from model import SiteAlbum
import labels

class ServiceUnavailable(HTTPException):
	def __init__(self):
		self.code = 503
		self.message = u"База данных пуста, зайдите позже. (Если нужно загрузить альбом, см. <a href='/api'>сюда</a>.)"

class Recent(BaseRequestHandler):
	xsltName = 'index.xsl'
	tabName = 'music'

	def get(self):
		self.check_access()
		offset = self.get_offset()
		xml = u"<index skip=\"%u\"><albums>" % offset
		xml += u''.join([a.shortxml for a in self.get_albums(offset)])
		xml += u'</albums>'
		xml += labels.load()
		xml += u'</index>'
		self.sendXML(xml, {
			'label': self.request.get('label'),
		})

	def get_albums(self, offset):
		label = self.request.get('label')
		if label:
			list = SiteAlbum.gql('WHERE labels = :1 ORDER BY release_date DESC', label)
		else:
			list = SiteAlbum.all().order('-release_date')
		result = list.fetch(16, offset)
		if not result and not offset:
			raise ServiceUnavailable()
		return result

	def get_offset(self):
		if self.request.get('skip'):
			return int(self.request.get('skip'))
		else:
			return 0
