# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import base64, hmac, hashlib

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
import model, myxml, mail

class APIHandler(BaseRequestHandler):
	def post(self):
		data = self.request.get('xml')

		if self.request.get('signature') != sign('xyz', data):
			return self.reply({
				'status': 'error',
				'message': 'Authentication failed.',
			})

		logging.info(u'API called with replace=%u and data: %s' % (int('0' + self.request.get('replace')), data))
		self.importAlbum(parseString(data.encode('utf-8')))

	def handle_exception(self, e, debug_mode):
		self.reply({
			'status': 'error',
			'message': str(e),
		})

	def sendXML(self, content):
		result = "<?xml version=\"1.0\"?>"
		result += content
		self.response.headers['Content-Type'] = 'application/xml; charset=utf-8'
		self.response.out.write(result)
		logging.debug(result)

	def reply(self, dict):
		self.sendXML(myxml.em(u'response', dict))

	def importAlbum(self, xml):
		for em in xml.getElementsByTagName('album'):
			try:
				artist = model.SiteArtist.gql('WHERE name = :1', em.attributes['artist'].value).get()
			except KeyError:
				raise Exception(u'/album/@artist not set')
			if not artist:
				artist = model.SiteArtist(name=em.attributes['artist'].value)
				artist.put(quick=True)

			album = model.SiteAlbum.gql('WHERE artist = :1 AND name = :2', artist, em.attributes['name'].value).get()
			if album is not None and not self.request.get('replace'):
				return self.reply({
					'status': 'error',
					'message': u'Альбом "%s" от %s уже есть.' % (album.name, artist.name),
					})
			if not album:
				album = model.SiteAlbum(artist=artist, name=em.attributes['name'].value)
			album.release_date = datetime.datetime.strptime(em.attributes["pubDate"].value[:10], '%Y-%m-%d').date()
			album.put(quick=True)

			self.importImages(album, em)
			self.importTracks(album, em)
			self.importFiles(album, em)

			album.put()

			mail.send('justin.forest@gmail.com', self.render('album-added.html', {
				'album_id': album.id,
				'album_name': album.name,
			}))

			self.sendXML(myxml.em(u'response', {
				'status': 'ok',
				'message': u'Album "%s" from %s is available at %s' % (album.name, artist.name, self.getBaseURL() + 'album/' + str(album.id)),
			}))

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
			track = model.SiteTrack(id=model.SiteTrack.getNextId(), album=album)
			track.title = em.attributes["title"].value
			track.number = int(em.attributes["number"].value)
			track.mp3_link = em.attributes["mp3"].value
			track.mp3_length = int(em.attributes["mp3-length"].value)
			track.duration = em.attributes["duration"].value
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

def sign(password, string):
	dm = hmac.new(password, string, hashlib.sha1)
	return base64.b64encode(dm.digest())
