# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

# Site imports.
import base
import model
import myxml

class Player(base.CachingRequestHandler):
	xsltName = 'player.xsl'
	tabName = 'music'

	def get_cached(self):
		xml = self.get_stats()
		self.sendXML(myxml.em(u'player', {
			'user': self.request.get('user'),
		}, xml))

	def get_stats(self):
		xml = u''
		wanted = self.get_album_ids()
		for artist in model.SiteArtist.all().fetch(1000):
			albums = u''
			for album in model.SiteAlbum.gql('WHERE artist = :1', artist).fetch(1000):
				if wanted is None or album.id in wanted:
					tracks = u''.join([t.xml for t in model.SiteTrack.gql('WHERE album = :1', album).fetch(1000)])
					albums += myxml.em(u'album', {
						'id': album.id,
						'name': album.name,
					}, tracks)
			if len(albums):
				xml += myxml.em(u'artist', {
					'id': artist.id,
					'name': artist.name,
					'sort': artist.sortname,
				}, albums)
		return myxml.em(u'artists', content=xml)

	def get_album_ids(self):
		if not self.request.get('user'):
			return None
		user = model.SiteUser.gql('WHERE nickname = :1', self.request.get('user')).get()
		return [a.album.id for a in model.SiteAlbumStar.gql('WHERE user = :1', user.user).fetch(1000)]

if __name__ == '__main__':
	base.run([
		('/player', Player),
	])
