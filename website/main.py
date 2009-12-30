# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

# Python imports
import logging, urllib

# GAE imports
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

# Site imports.
from base import BaseRequestHandler, run
from s3 import S3SettingsHandler, S3UploadHandler
import api
import model
import album
import artist
import sitemap
import tracks
import upload

class MainHandler(BaseRequestHandler):
	def get(self):
		self.response.out.write('Hello world!')


class IndexHandler(BaseRequestHandler):
	def get(self):
		offset = self.get_offset()
		xml = u"<index skip=\"%u\"><albums>" % offset
		for album in self.get_albums(offset):
			if album.xml:
				xml += album.xml
		xml += u'</albums></index>'
		self.sendXML(xml, {
			'label': self.request.get('label'),
		})

	def get_albums(self, offset):
		label = self.request.get('label')
		if label:
			list = model.SiteAlbum.gql('WHERE labels = :1 ORDER BY release_date DESC', label)
		else:
			list = model.SiteAlbum.all().order('-release_date')
		return list.fetch(15, offset)

	def get_offset(self):
		if self.request.get('skip'):
			return int(self.request.get('skip'))
		else:
			return 0


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


if __name__ == '__main__':
	run([
		('/', IndexHandler),
		('/add/file', AddFileHandler),
		('/api/queue\.xml', api.Queue),
		('/api/queue\.yaml', api.Queue),
		('/api/queue/delete', api.Delete),
		('/api/submit/album', api.SubmitAlbum),
		('/submit', SubmitHandler),
		('/album/(\d+)$', album.Viewer),
		('/album/(\d+)/edit$', album.Editor),
		('/album/update-xml', album.XmlUpdater),
		('/albums\.rss', album.RSSHandler),
		('/upload', S3UploadHandler),
		('/upload/remote', upload.Remote),
		('/upload/settings', S3SettingsHandler),
		('/artist/fix', artist.FixHandler),
		('/artist/(\d+)$', artist.ViewHandler),
		('/artists\.rss', artist.RSSHandler),
		('/robots.txt', sitemap.RobotsHandler),
		('/sitemap.xml', sitemap.SitemapHandler),
		('/track/(\d+)$', tracks.Viewer),
		('/tracks\.rss', tracks.RSSHandler),
	])
