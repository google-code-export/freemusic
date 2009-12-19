# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

# Python imports
import logging, urllib

# GAE imports
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

# Site imports.
from base import BaseRequestHandler, run
import model


class MainHandler(BaseRequestHandler):
	def get(self):
		self.response.out.write('Hello world!')


class IndexHandler(BaseRequestHandler):
	def get(self):
		xml = u""
		for album in model.SiteAlbum.all().order('-release_date').fetch(10):
			if album.xml:
				xml += album.xml
		self.sendXML(u'<index>' + xml + u'</index>')


class SubmitHandler(BaseRequestHandler):
	def get(self):
		self.render('submit.html')

	def post(self):
		artist = self.get_artist(self.request.get('artist'))
		album = self.get_album(self.request.get('album'), artist)

		logging.info('New album "%s" from %s' % (album.name, artist.name))
		next = '/music/' + self.quote(artist.name) + '/' + self.quote(album.name) + '/'
		self.redirect(next)

	def get_artist(self, name):
		artist = model.SiteArtist.gql('WHERE name = :1', name).get()
		if not artist:
			artist = model.SiteArtist(name=name)
			artist.put()
		return artist

	def get_album(self, name, artist):
		album = model.SiteAlbum.gql('WHERE artist = :1 AND name = :2', artist, name).get()
		if not album:
			album = model.SiteAlbum(name=name, artist=artist)
			album.put()
		return album


class AddFileHandler(BaseRequestHandler):
	@login_required
	def get(self):
		self.render('add-file.html', {
			'artist': self.request.get('artist'),
			'album': self.request.get('album'),
		})


class AlbumHandler(BaseRequestHandler):
	def get(self, artist_name, album_name):
		# TODO: filter by artist
		album = model.SiteAlbum.gql('WHERE name = :1', album_name).get()
		if album:
			self.sendXML(album.xml)

if __name__ == '__main__':
	run([
		('/', IndexHandler),
		('/add/file', AddFileHandler),
		('/submit', SubmitHandler),
		('/music/([^/]+)/([^/]+)/', AlbumHandler),
	])
