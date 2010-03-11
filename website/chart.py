# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

from logging import debug as log

import base
import lastfm
import model
import myxml

class ShowChart(base.CachingRequestHandler):
	xsltName = 'chart.xsl'
	tabName = 'chart'

	def get_cached(self):
		xml = u''
		for artist in model.SiteArtist.all().fetch(1000):
			if artist.name != 'Various Artists' and artist.name != 'Error':
				tmp = lastfm.get_artist(artist.name)
				xml += myxml.em(u'artist', {
					'id': artist.id,
					'name': artist.name,
					'lastfm-url': tmp.find('artist/url').text,
					'playcount': tmp.find('artist/stats/playcount').text,
					'listeners': tmp.find('artist/stats/listeners').text,
					})
		xml = u'<chart>' + xml + u'</chart>'
		return xml
