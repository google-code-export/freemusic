# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

# Python imports
import logging, urllib

# GAE imports
from google.appengine.ext.webapp.util import login_required

# Site imports.
from base import BaseRequestHandler, run
import api
import chart
import clips
import events
import index
import model
import reviews
import settings
import tracks
import upload

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
		('/album/(\d+)/reviews\.rss$', reviews.AlbumRSS),
		('/api', api.Index),
		('/api/submit/album', api.SubmitAlbum),
		('/api/update', api.Update),
		('/api/dump\.json', api.Dump),
		('/chart', chart.ShowChart),
		('/clips', clips.ShowClips),
		('/clips/random\.json', clips.GetRandomClip),
		('/clips/recent.xml', clips.GetRecentClips),
		('/events', events.All),
		('/events/update', events.Update),
		('/reviews', reviews.ShowReviews),
		('/reviews\.rss', reviews.AllRSS),
		('/settings', settings.SettingsPage),
		('/submit', SubmitHandler),
		('/track/(\d+)$', tracks.Viewer),
		('/tracks\.rss', tracks.RSSHandler),
	])
