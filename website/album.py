# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

from logging import debug as log

from base import BaseRequestHandler
from model import SiteAlbum

class XmlUpdater(BaseRequestHandler):
	def get(self):
		for album in SiteAlbum.all().fetch(1000):
			album.put()
			log('album/%u: xml updated' % album.id)
		self.redirect('/')
