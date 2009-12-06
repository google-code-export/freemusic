# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

# Python imports
import datetime, time
import logging
from xml.dom.minidom import parseString

# GAE imports
import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import login_required

# Site imports
from base import BaseRequestHandler
import model

class UploadXmlHandler(BaseRequestHandler):
	@login_required
	def get(self):
		self.render('upload-xml.xml')

	def post(self):
		if not users.is_current_user_admin():
			raise Exception('You are not an admin.')

		self.importArtists(parseString(self.request.get('xml')))

		self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
		self.response.out.write(self.request.get('xml'))

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
		for em in xml.getElementsByTagName("album"):
			name = em.attributes["name"].value
			album = model.SiteAlbum.gql('WHERE artist = :1 AND name = :2', artist, name).get()
			if album is None:
				album = model.SiteAlbum(artist=artist, name=name)
				album.put()
				logging.info("+ album %s (%s)" % (album.name, artist.name))

			album.release_date = datetime.datetime.strptime(em.attributes["pubDate"].value[:10], '%Y-%m-%d').date()
			album.put()

			self.importImages(album, em)
			self.importTracks(album, em)
			self.importFiles(album, em)

	def importImages(self, album, xml):
		self.purge(model.SiteImage, album)
		for em in xml.getElementsByTagName("image"):
			image = model.SiteImage(album=album)
			image.uri = em.attributes["uri"].value
			image.width = int(em.attributes["width"].value)
			image.height = int(em.attributes["height"].value)
			if "yes" == em.attributes["cover"].value:
				image.cover = True
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

if __name__ == '__main__':
	application = webapp.WSGIApplication([
		('/upload/xml', UploadXmlHandler),
	], debug=True)
	wsgiref.handlers.CGIHandler().run(application)
