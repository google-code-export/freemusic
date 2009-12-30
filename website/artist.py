# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:
#
# Классы для работы с артистами.

from logging import debug as log

from google.appengine.ext import db

from base import HTTPException
from rss import RSSHandler as BaseRequestHandler
from model import SiteArtist
import myxml as xml

class FixHandler(BaseRequestHandler):
	def get(self):
		maxid = 0

		lst = SiteArtist.all().fetch(1000)
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

class ViewHandler(BaseRequestHandler):
	def get(self, id):
		artist = SiteArtist.gql('WHERE id = :1', int(id)).get()
		if artist and artist.xml:
			self.sendXML(artist.xml)
		raise HTTPException(404, u'Нет такого исполнителя.')

class RSSHandler(BaseRequestHandler):
	def get(self):
		items = [{
			'title': u'Новый исполнитель: ' + artist.name,
			'link': 'artist/' + str(artist.id),
		} for artist in SiteArtist.all().order('-id').fetch(20)]
		self.sendRSS(items, title=u'Новые исполнители')
