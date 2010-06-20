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
		# Информация о расположении текущей страницы.
		pager = self.get_pager()
		# Выводим страницу.
		return self.send_html('index.html', {
			'albums': self.get_albums(pager['start'] - 1),
			'pager': pager,
			'label': self.request.get('label'),
		})

	def get_album_count(self):
		return self.get_query().count()

	def get_albums(self, offset):
		result = self.get_query().fetch(16, offset)
		if not result and not offset:
			raise ServiceUnavailable()
		return result

	def get_query(self):
		label = self.request.get('label')
		if label:
			return model.SiteAlbum.gql('WHERE labels = :1 ORDER BY release_date DESC', label)
		else:
			return model.SiteAlbum.all().order('-release_date')

	def get_pager(self):
		page = max(int(self.request.get('page') or 1), 1)
		offset = ((page - 1) * 16)
		total = self.get_album_count()
		pages = int(math.ceil(float(total) / 16))

		return {
			'page': page,
			'pages': pages,
			'start': offset + 1,
			'end': min(offset + 15, total),
			'total': total,
			'pagenumbers': range(max(1, page - 5), min(page + 5, pages + 1)),
		}

if __name__ == '__main__':
	base.run([
		('/', Recent),
	])
