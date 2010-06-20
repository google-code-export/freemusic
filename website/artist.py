# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:
#
# Классы для работы с артистами.

from logging import debug as log

from google.appengine.ext import db

import base
import rss
import model
import myxml

class ShowArtist(base.BaseRequestHandler):
	"""
	Вывод информации об исполнителе.
	"""

	tabName = 'music'

	def get(self, id):
		artist = model.SiteArtist.gql('WHERE id = :1', long(id)).get()
		if not artist:
			raise HTTPException(404, u'Нет такого исполнителя.')

		self.send_html('artist.html', {
			'artist': artist,
			'albums': model.SiteAlbum.gql('WHERE artist = :1 ORDER BY release_date', artist).fetch(100),
		})

	def get_albums_xml(self, artist, reviews):
		xml = u''
		for a in model.SiteAlbum.gql('WHERE artist = :1', artist).fetch(100):
			xml += a.shortxml
			self.get_reviews_xml(a, reviews)
		if len(xml):
			xml = myxml.em(u'albums', content=xml)
		return xml

	def get_reviews_xml(self, album, reviews):
		for r in model.SiteAlbumReview.gql('WHERE album = :1', album).fetch(100):
			reviews.append(myxml.em(u'review', {
				'album-id': album.id,
				'album-name': album.name,
				'average': r.rate_average,
				'pubDate': r.published,
				'author': r.author.nickname,
			}))

	def get_events_xml(self, artist):
		xml = u''
		for e in model.Event.gql('WHERE artist = :1', artist).fetch(100):
			xml += e.xml
		if len(xml):
			xml = myxml.em(u'events', content=xml)
		return xml

class List(base.BaseRequestHandler):
	def get(self):
		self.send_html('artist-list.html', {
			'artists': model.SiteArtist.all().order('sortname').fetch(100),
		})

if __name__ == '__main__':
	base.run([
		('/artist/(\d+)$', ShowArtist),
		('/artist', List),
	])
