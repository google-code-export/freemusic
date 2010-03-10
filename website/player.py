# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

# Site imports.
import base
import model
import myxml

class Player(base.BaseRequestHandler):
	xsltName = 'player.xsl'
	tabName = 'music'

	def get(self):
		tracks = model.SiteTrack.all()
		xml = u''.join([t.to_xml() for t in tracks.fetch(1000)])
		self.sendXML(myxml.em(u'player', content=xml))

if __name__ == '__main__':
	base.run([
		('/player', Player),
	])
