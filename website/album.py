# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

from logging import debug as log
import datetime

from google.appengine.api import users
from google.appengine.ext import db

from base import BaseRequestHandler, HTTPException, ForbiddenException
from model import SiteAlbum, SiteImage, SiteTrack, SiteFile
from index import Recent
import rss, myxml

class SiteAlbumStar(db.Model):
	"Хранит информацию о любимых альбомах пользователей."
	album = db.ReferenceProperty(SiteAlbum)
	user = db.UserProperty()

class XmlUpdater(BaseRequestHandler):
	def get(self):
		self.check_access()
		for album in SiteAlbum.all().fetch(1000):
			album.put()
		self.redirect('/')

class Viewer(BaseRequestHandler):
	xsltName = 'albums.xsl'

	def get(self, id):
		self.check_access()
		self.sendXML(self.get_album(id).xml)

	def get_album(self, id):
		if id:
			album = SiteAlbum.gql('WHERE id = :1', int(id)).get()
			if album:
				return album
		raise HTTPException(404, u'Нет такого альбома.')

class JSON(Viewer):
	def get(self):
		self.sendJSON([{
			'id': int(track.id),
			'ogg': str(track.ogg_link),
			'mp3': str(track.mp3_link),
		} for track in self.get_album(self.request.get('id')).tracks()])

class Editor(Viewer):
	xsltName = 'albums.xsl'

	def get(self, id):
		self.check_access()
		self.sendXML('<form>' + self.get_album(id).xml + '</form>')

	def post(self, id):
		try:
			album = self.get_album(id)
			self.force_user_or_admin(album.owner)

			album.name = self.request.get(u'name')
			album.release_date = datetime.datetime.strptime(self.request.get(u'pubDate'), '%Y-%m-%d').date()
			album.text = self.request.get(u'text')
			album.labels = [unicode(label.strip()).lower() for label in self.request.get('labels').split(',')]

			# Переименовываем дорожки
			self.rename_tracks(album)

			album.put()
			album.artist.put() # обновление XML

			self.redirect('/album/' + str(album.id))
		except Exception, e:
			log([(arg, self.request.get(arg)) for arg in self.request.arguments()])
			raise

	def rename_tracks(self, album):
		"Извлекает из запроса номера и имена дорожек, сохраняет их."
		data = {}
		for arg in self.request.arguments():
			if arg.startswith('track.') and self.request.get(arg):
				data[int(arg.split('.', 1)[1])] = self.request.get(arg)
		if data:
			for track in SiteTrack.gql('WHERE album = :1', album).fetch(1000):
				if track.id in data:
					track.title = data[track.id]
					track.put()


class Delete(Viewer):
	xsltName = 'albums.xsl'

	def get(self, id):
		album = self.get_album(id)
		self.sendXML(myxml.em(u'delete-album', {
			'id': album.id,
			'name': album.name,
			'artist-id': album.artist.id,
			'artist-name': album.artist.name,
		}))

	def post(self, id):
		album = self.get_album(id)
		for cls in (SiteImage, SiteTrack, SiteFile):
			items = cls.gql('WHERE album = :1', album).fetch(1000)
			if items:
				for item in items:
					item.delete()

		artist = album.artist
		album.delete()

		artist.put() # обновление XML
		self.redirect('/artist/' + str(artist.id))

	def get_album(self, id):
		album = Viewer.get_album(self, id)
		user = self.force_user()
		if album.owner != user and not self.is_admin():
			raise ForbiddenException
		return album

class RSSHandler(rss.RSSHandler):
	def get(self):
		items = [{
			'title': album.name,
			'link': 'album/' + str(album.id),
		} for album in SiteAlbum.all().order('-release_date').fetch(20)]
		self.sendRSS(items, title=u'Новые альбомы')

class Stars(BaseRequestHandler):
	def get(self):
		if self.request.get('id'):
			album = SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
			a = SiteAlbumStar.gql('WHERE user = :1 AND album = :2', self.force_user(), album).get()
			if a is not None:
				return self.sendJSON({
					'star': 1,
				})
		self.sendJSON({
			'star': 0,
		})

	def post(self):
		album = SiteAlbum.gql('WHERE id = :1', int(self.request.get('id'))).get()
		if album is not None:
			user = self.force_user()
			star = SiteAlbumStar.gql('WHERE user = :1 AND album = :2', user, album).get()

			status = self.request.get('status') == 'true'
			if status and not star:
				SiteAlbumStar(user=user, album=album).put()
			elif not status and star:
				star.delete()

			if status:
				return self.sendJSON({'notify':1})
		self.sendJSON({'notify':0})

class Collection(Recent):
	xsltName = 'collection.xsl'

	def get_albums(self, offset):
		return [star.album for star in SiteAlbumStar.gql('WHERE user = :1', self.force_user()).fetch(1000)]
