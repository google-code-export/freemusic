# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

from logging import debug as log

from google.appengine.api import memcache

import base
import lastfm
import model
import myxml

class ShowChart(base.BaseRequestHandler):
	xsltName = 'chart.xsl'

	def get(self):
		data = self.get_xml()
		self.sendXML(data)

	def get_xml(self):
		xml = memcache.get('/chart')
		if xml is None or ('update' in self.request.arguments() and self.is_admin()):
			xml = u''
			for artist in model.SiteArtist.all().fetch(1000):
				if artist.name != 'Various Artists':
					tmp = lastfm.get_artist(artist.name)
					xml += myxml.em(u'artist', {
						'id': artist.id,
						'name': artist.name,
						'lastfm-url': tmp.find('artist/url').text,
						'playcount': tmp.find('artist/stats/playcount').text,
						'listeners': tmp.find('artist/stats/listeners').text,
						})
			xml = u'<chart>' + xml + u'</chart>'
			memcache.set('/chart', xml)
		return xml
