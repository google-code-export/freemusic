# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import re

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

class NowPlaying(base.CachingRequestHandler):
	cacheTTL = 10

	def get_cached(self):
		data = { 'html': None }
		data['artist'], data['title'] = get_current_info()

		artist = model.SiteArtist.gql('WHERE name = :1', data['artist']).get()
		if artist is not None:
			data['html'] = u'%s (<a href="/artist/%u" target="_blank">%s</a>)' % (data['title'], artist.id, artist.name)
		elif data['artist']:
			data['html'] = u'%s (%s)' % (data['title'], data['artist'])
		elif data['title']:
			data['html'] = data['title']
		else:
			data['html'] = u'???'
		data['ttl'] = self.cacheTTL

		self.sendJSON(data)

if __name__ == '__main__':
	base.run([
		('/radio', ShowRadio),
		('/radio/current.json', NowPlaying),
	])
