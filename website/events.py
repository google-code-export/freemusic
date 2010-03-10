# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

from logging import debug as log
import datetime

import base
import lastfm
import model
import myxml
import util

class Update(base.BaseRequestHandler):
	def get(self):
		if self.is_cron() or self.is_admin():
			for artist in model.SiteArtist.all().fetch(1000):
				if artist.name != 'Various Artists':
					self.update_events_for(artist)
		else:
			self.redirect('/')

	def update_events_for(self, artist):
		"""
		Удаляет существующие события для исполнителя, загружает новые.
		"""
		for old in model.SiteEvent.gql('WHERE artist = :1', artist).fetch(1000):
			old.delete()
		tree = lastfm.get_events(artist.name)
		for event in tree.findall('.//event'):
			try:
				if event.find('cancelled').text == '0':
					e = model.SiteEvent(artist=artist)
					e.id = int(event.find('id').text)
					e.xml = myxml.em('event', {
						'artist-id': artist.id,
						'artist-name': artist.name,
						'title': event.find('title').text,
						'date': datetime.datetime.strptime(event.find('startDate').text, '%a, %d %b %Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'),
						'venue': event.find('venue/name').text,
						'city': event.find('venue/location/city').text,
						'url': event.find('url').text,
					})
					e.put()
			except:
				pass

class All(base.BaseRequestHandler):
	xsltName = 'events.xsl'
	tabName = 'events'

	def get(self):
		xml = u''.join([e.xml for e in model.SiteEvent.all().fetch(1000)])
		self.sendXML(myxml.em(u'events', content=xml))
