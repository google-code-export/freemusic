# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

# Python imports
import datetime, time
import logging
import urllib
from xml.dom.minidom import parseString

# GAE imports
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp.util import login_required

# Site imports
from base import BaseRequestHandler, run
import model

class UploadHandler(BaseRequestHandler):
	@login_required
	def get(self):
		worker = 'upload.' + self.request.environ['HTTP_HOST']
		self.sendXML('<upload worker="%s"/>' % urllib.quote(worker))

class UploadXmlHandler(BaseRequestHandler):
	@login_required
	def get(self):
		self.render('upload-xml.xml')

	def post(self):
		if not users.is_current_user_admin():
			raise Exception('You are not an admin.')

		self.importArtists(parseString(self.request.get('xml')))
		self.redirect('/')

	def importArtists(self, xml):
		for em in xml.getElementsByTagName("artist"):
			name = em.attributes["name"].value
			artist = model.SiteArtist.gql('WHERE name = :1', name).get()
			if artist is None:
				artist = model.SiteArtist(name=name)
				artist.put()
				logging.info("+ artist %s" % artist.name)

			self.importAlbums(artist, em)

	def importAlbums(self, artist, xml):
		last = model.SiteAlbum.gql('ORDER BY id DESC').get()
		if last:
			nextId = last.id + 1
		else:
			nextId = 1

		for em in xml.getElementsByTagName("album"):
			name = em.attributes["name"].value
			logging.info('Processing album "%s" by %s' % (name, artist.name))
			album = model.SiteAlbum.gql('WHERE artist = :1 AND name = :2', artist, name).get()
			if album is None:
				album = model.SiteAlbum(id=nextId, artist=artist, name=name)
				logging.info("+ album %s (%s), id=%u" % (album.name, artist.name, album.id))
				nextId += 1

			album.release_date = datetime.datetime.strptime(em.attributes["pubDate"].value[:10], '%Y-%m-%d').date()
			album.put(quick=True)

			self.importImages(album, em)
			self.importTracks(album, em)
			self.importFiles(album, em)

			album.put() # updates XML

	def importImages(self, album, xml):
		self.purge(model.SiteImage, album)
		for em in xml.getElementsByTagName("image"):
			image = model.SiteImage(album=album)
			image.uri = em.attributes["uri"].value
			image.width = int(em.attributes["width"].value)
			image.height = int(em.attributes["height"].value)
			image.type = em.attributes["type"].value
			image.put()

	def importTracks(self, album, xml):
		self.purge(model.SiteTrack, album)
		for em in xml.getElementsByTagName("track"):
			track = model.SiteTrack(album=album)
			track.title = em.attributes["title"].value
			track.number = int(em.attributes["number"].value)
			track.mp3_link = em.attributes["mp3"].value
			track.put()

	def importFiles(self, album, xml):
		self.purge(model.SiteFile, album)
		for em in xml.getElementsByTagName("file"):
			track = model.SiteFile(album=album)
			track.name = em.attributes["name"].value
			track.uri = em.attributes["uri"].value
			track.type = em.attributes["type"].value
			if em.attributes["size"].value:
				track.size = int(em.attributes["size"].value)
			track.put()

	def purge(self, source, album):
		old = source.gql('WHERE album = :1', album).fetch(1000)
		if old:
			db.delete(old)
