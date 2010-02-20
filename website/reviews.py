# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

from rss import RSSHandler
from base import HTTPException
from model import SiteAlbum, SiteAlbumReview

class AlbumRSS(RSSHandler):
	def get(self, album_id):
		album = SiteAlbum.gql('WHERE id = :1', int(album_id)).get()
		if album is None:
			raise HTTPException(404, 'Нет такого альбома.')
		entries = [r.to_rss() for r in SiteAlbumReview.gql('WHERE album = :1 ORDER BY published DESC', album).fetch(10)]
		self.sendRSS(entries, title=u'Рецензии на "%s" от %s' % (album.name, album.artist.name))

class AllRSS(RSSHandler):
	def get(self):
		entries = [r.to_rss() for r in SiteAlbumReview.all().order('-published').fetch(10)]
		self.sendRSS(entries, title=u'Все Рецензии')
