# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import re

from google.appengine.api import memcache

import base
import model
import myxml
import util

def get_current_info():
	data = util.fetch('http://radio.deadchannel.ru/')
	if data is not None:
		m = re.search('<td>Current Song:</td>\s*<td class="streamdata">(.*)</td>', data)
		if m is not None:
			parts = m.group(1).split('-', 1)
			if len(parts) == 2:
				return (parts[0].strip(), parts[1].strip())
			return (None, parts[0].strip())
	return (None, None)

class ShowRadio(base.BaseRequestHandler):
	xsltName = 'radio.xsl'
	tabName = 'music'

	def get(self):
		self.sendXML(u'<radio/>')

class NowPlaying(base.BaseRequestHandler):
	def get(self):
		cached = memcache.get(self.request.path)
		if cached is None:
			cached = { 'html': None }
			cached['artist'], cached['title'] = get_current_info()

			artist = model.SiteArtist.gql('WHERE name = :1', cached['artist']).get()
			if artist is not None:
				cached['html'] = u'%s (<a href="/artist/%u" target="_blank">%s</a>)' % (cached['title'], artist.id, artist.name)
			elif cached['artist']:
				cached['html'] = u'%s (%s)' % (cached['title'], cached['artist'])
			elif cached['title']:
				cached['html'] = cached['title']
			else:
				cached['html'] = u'???'

			memcache.set(self.request.path, cached, 60)
		self.sendJSON(cached)

if __name__ == '__main__':
	base.run([
		('/radio', ShowRadio),
		('/radio/current.json', NowPlaying),
	])
