# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import sys
import math

# Site imports.
import base
import model
import labels

class ServiceUnavailable(base.HTTPException):
	def __init__(self):
		self.code = 503
		self.message = u"База данных пуста, зайдите позже. (Если нужно загрузить альбом, см. <a href='/api'>сюда</a>.)"

class Recent(base.BaseRequestHandler):
	template = 'index.html'
	tabName = 'music'

	def get(self):
		# Загружаем интересующие альбомы.
		albums = model.SiteAlbum.all().order('-release_date').fetch(16)
		# Разбиваем на группы по 4.
		groups = [albums[x*4:x*4+4] for x in range(math.ceil(len(albums) / 4))]
		# Возвращаем.
		return self.send_html('index.html', {
			'groups': groups,
		})

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
			list = model.SiteAlbum.gql('WHERE labels = :1 ORDER BY release_date DESC', label)
		else:
			list = model.SiteAlbum.all().order('-release_date')
		result = list.fetch(16, offset)
		if not result and not offset:
			raise ServiceUnavailable()
		return result

	def get_offset(self):
		if self.request.get('skip'):
			return int(self.request.get('skip'))
		else:
			return 0

if __name__ == '__main__':
	base.run([
		('/', Recent),
	])
