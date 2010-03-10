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
		xml = self.get_stats()
		xml += myxml.em(u'tracks', content=u''.join([t.to_xml() for t in tracks.fetch(1000)]))
		self.sendXML(myxml.em(u'player', content=xml))

	def get_stats(self):
		xml = u''
		for artist in model.SiteArtist.all().fetch(1000):
			albums = u''
			for album in model.SiteAlbum.gql('WHERE artist = :1', artist).fetch(1000):
				albums += myxml.em(u'album', {
					'id': album.id,
					'name': album.name,
				})
			xml += myxml.em(u'artist', {
				'id': artist.id,
				'name': artist.name,
				'sort': artist.sortname,
			}, albums)
		return myxml.em(u'artists', content=xml)

if __name__ == '__main__':
	base.run([
		('/player', Player),
	])
