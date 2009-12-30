# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:
#
# Работа с дорожками, пока только выдаёт подкаст.

from logging import debug as log

from model import SiteTrack
from rss import RSSHandler as RssBase
from base import BaseRequestHandler
import myxml as xml

class RSSHandler(RssBase):
	def get(self):
		self.sendRSS([{
			'title': track.title,
			'link': 'track/' + str(track.id),
			'_': xml.em(u'enclosure', {
				'length': track.mp3_length,
				'type': 'audio/mpeg',
				'url': track.mp3_link,
			}),
		} for track in SiteTrack.all().order('-id').fetch(50)], title=u'Новая музыка')

class Viewer(BaseRequestHandler):
	def get(self, id):
		track = SiteTrack.gql('WHERE id = :1', int(id)).get()
		if not track:
			raise Exception('No such track.')
		self.sendXML(track.to_xml())
