# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

from logging import debug as log
import datetime

from google.appengine.api import users

from base import BaseRequestHandler
from model import SiteAlbum
import rss

class XmlUpdater(BaseRequestHandler):
	def get(self):
		for album in SiteAlbum.all().fetch(1000):
			album.put()
		self.redirect('/')

class Viewer(BaseRequestHandler):
	def get(self, id):
		self.sendXML(self.get_album(id).xml)

	def get_album(self, id):
		album = SiteAlbum.gql('WHERE id = :1', int(id)).get()
		if album:
			return album
		raise Exception('No such album.')

class Editor(Viewer):
	def get(self, id):
		self.sendXML('<form>' + self.get_album(id).xml + '</form>')

	def post(self, id):
		log(self.request.arguments())

		album = self.get_album(id)
		self.force_user_or_admin(album.owner)

		album.name = self.request.get(u'name')
		album.release_date = datetime.datetime.strptime(self.request.get(u'pubDate'), '%Y-%m-%d').date()
		album.text = self.request.get(u'text')
		album.labels = [unicode(label.strip()).lower() for label in self.request.get('labels').split(',')]

		album.put()
		album.artist.put() # обновление XML

		self.redirect('/album/' + str(album.id))

class RSSHandler(rss.RSSHandler):
	def get(self):
		items = [{
			'title': album.name,
			'link': 'album/' + str(album.id),
		} for album in SiteAlbum.all().order('-release_date').fetch(20)]
		self.sendRSS(items, title=u'Новые альбомы')
