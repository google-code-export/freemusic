# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:
#
# Содержит класс RSSHandler, генерирующий валидный RSS поток,
# соответствующий рекоммендациям <http://beta.feedvalidator.org/>.

from logging import debug as log
from base import BaseRequestHandler
import myxml as xml

class RSSHandler(BaseRequestHandler):
	def sendRSS(self, items, title=None, link='', description=None):
		base = self.getBaseURL()
		content = u''

		if not title:
			title = u'Новости сайта ' + self.getHost()
		if not description:
			description = title

		content += xml.em(u'title', content=title)
		content += xml.em(u'link', content=base + link)
		content += xml.em(u'description', content=xml.escape(description))
		content += xml.em(u'atom:link', {
			'href': self.request.url,
			'rel': 'self',
			'type': 'application/rss+xml',
		})
		content += xml.em(u'language', content=u'ru')

		for item in items:
			entry = xml.em(u'title', content=xml.escape(item['title']))
			entry += xml.em(u'link', content=base + item['link'])
			if 'description' not in item.keys():
				item['description'] = item['title']
			entry += xml.em(u'description', content=xml.escape(item['description']))
			entry += xml.em(u'guid', {'isPermaLink': 'true'}, content=base + item['link'])
			if '_' in item.keys():
				entry += item['_']
			content += xml.em(u'item', content=entry)
		self.response.headers['Content-Type'] = 'text/xml; charset=utf-8'
		self.response.out.write(xml.em(u'rss', {'version': '2.0', 'xmlns:atom': 'http://www.w3.org/2005/Atom'}, xml.em(u'channel', content=content)))
