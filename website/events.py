# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import re
import logging
import datetime

from google.appengine.api.labs import taskqueue

import base
import lastfm
import model
import myxml
import util

class Update(base.BaseRequestHandler):
	def get(self):
		if not self.is_cron() and not self.is_admin():
			raise Exception('No access for you.')

		for artist in model.SiteArtist.all().fetch(1000):
			if artist.lastfm_name:
				try:
					taskqueue.Task(url='/events/update', name=re.sub('[^a-zA-Z0-9]', '-', artist.name), params={ 'artist': artist.id }).add(queue_name='events-update')
				except: pass
		self.sendText('Updates scheduled.')

	def post(self):
		if not self.is_cron() and not self.is_admin():
			raise Exception('No access for you.')
		if not self.request.get('artist'):
			raise Exception('Artist is not specified.')
		self.update_events_for(model.SiteArtist.gql('WHERE id = :1', int(self.request.get('artist'))).get())

	def update_events_for(self, artist):
		"""
		Удаляет существующие события для исполнителя, загружает новые.
		"""
		logging.debug('Deleting old events for %s' % artist.name)
		for old in model.Event.gql('WHERE artist = :1', artist).fetch(1000): old.delete()

		count = 0
		tree = lastfm.get_events(artist.lastfm_name)
		for event in tree.findall('.//event'):
			try:
				if event.find('cancelled').text == '0':
					e = model.Event(artist=artist)
					e.lastfm_id = int(event.find('id').text)
					e.title = event.find('title').text
					e.date = datetime.datetime.strptime(event.find('startDate').text, '%a, %d %b %Y %H:%M:%S')
					e.venue = event.find('venue/name').text
					e.city = event.find('venue/location/city').text
					e.url = event.find('url').text
					e.put()
					count += 1
			except Exception, e:
				logging.error('Error importing an event: %s' % e)
		if count: logging.info('%u events found for %s' % (count, artist.name.encode('utf-8')))

class All(base.BaseRequestHandler):
	tabName = 'events'

	def get(self):
		self.send_html('events.html', {
			'events': model.Event.all().order('date').fetch(1000)
		})
