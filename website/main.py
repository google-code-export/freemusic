# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

# Python imports
import logging, urllib

# GAE imports
from google.appengine.ext.webapp.util import login_required

# Site imports.
from base import BaseRequestHandler, run
from s3 import S3SettingsHandler, S3UploadHandler
import album
import api
import artist
import index
import labels
import model
import sitemap
import tracks
import upload
import users

class SubmitHandler(BaseRequestHandler):
	def get(self):
		self.check_access()
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
		('/', index.Recent),
		('/add/file', AddFileHandler),
		('/album/(\d+)$', album.Viewer),
		('/album/(\d+)/edit$', album.Editor),
		('/album/(\d+)/delete$', album.Delete),
		('/album/update-xml', album.XmlUpdater),
		('/albums\.rss', album.RSSHandler),
		('/api', api.Index),
		('/api/album/tracks\.json', album.JSON),
		('/api/queue\.xml', api.Queue),
		('/api/queue\.yaml', api.Queue),
		('/api/queue/delete', api.Delete),
		('/api/submit/album', api.SubmitAlbum),
		('/artist/fix', artist.FixHandler),
		('/artist/(\d+)$', artist.ViewHandler),
		('/artists', artist.List),
		('/artists\.rss', artist.RSSHandler),
		('/labels', labels.List),
		('/robots.txt', sitemap.RobotsHandler),
		('/sitemap.xml', sitemap.SitemapHandler),
		('/submit', SubmitHandler),
		('/track/(\d+)$', tracks.Viewer),
		('/tracks\.rss', tracks.RSSHandler),
		('/upload', S3UploadHandler),
		('/upload/remote', upload.Remote),
		('/upload/settings', S3SettingsHandler),
		('/users', users.List),
		('/users/invite', users.Invite),
	])
