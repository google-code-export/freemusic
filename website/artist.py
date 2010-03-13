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

class FixHandler(rss.RSSHandler):
	def get(self):
		maxid = 0

		lst = model.SiteArtist.all().fetch(1000)
		for artist in lst:
			if artist.id:
				maxid = max(maxid, artist.id)

		for artist in lst:
			if not artist.id:
				artist.id = maxid + 1
				maxid += 1
				log('saving artist %u(%s)' % (artist.id, artist.name))
			artist.put()

		self.redirect('/')

class ShowArtist(base.BaseRequestHandler):
	"""
	Вывод информации об исполнителе.
	"""

	xsltName = 'artists.xsl'
	tabName = 'music'

	def get(self, id):
		self.check_access()
		artist = model.SiteArtist.gql('WHERE id = :1', long(id)).get()
		if not artist or not artist.xml:
			raise HTTPException(404, u'Нет такого исполнителя.')

		reviews = []
		xml = self.get_albums_xml(artist, reviews)
		if len(reviews):
			xml += myxml.em(u'reviews', content=u''.join(reviews))
		xml += self.get_events_xml(artist)

		self.sendXML(myxml.em(u'artist', {
			'id': artist.id,
			'name': artist.name,
		}, content=xml))

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
		for e in model.SiteEvent.gql('WHERE artist = :1', artist).fetch(100):
			xml += e.xml
		if len(xml):
			xml =myxml.em(u'events', content=xml)
		return xml

class RSSHandler(base.BaseRequestHandler):
	def get(self):
		items = [{
			'title': u'Новый исполнитель: ' + artist.name,
			'link': 'artist/' + str(artist.id),
		} for artist in model.SiteArtist.all().order('-id').fetch(20)]
		self.sendRSS(items, title=u'Новые исполнители')

class List(base.BaseRequestHandler):
	xsltName = 'artists.xsl'
	tabName = 'music'

	def get(self):
		self.check_access()
		self.sendXML(xml.em(u'artists', content=u''.join([xml.em(u'artist', {
			'id': artist.id,
			'name': artist.name,
			'sortname': artist.sortname,
		}) for artist in model.SiteArtist.all().fetch(1000)])))

if __name__ == '__main__':
	base.run([
		('/artist/fix', FixHandler),
		('/artist/(\d+)$', ShowArtist),
		('/artists', List),
		('/artists\.rss', RSSHandler),
	])
