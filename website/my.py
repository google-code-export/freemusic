# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import base
import model

class My(base.BaseRequestHandler):
	xsltName = 'my.xsl'

	def get(self):
		user = model.SiteUser.gql('WHERE user = :1', self.force_user()).get()
		xml = u'<albums>' + u''.join([star.album.xml for star in model.SiteAlbumStar.gql('WHERE user = :1', self.force_user()).fetch(1000)]) + u'</albums>'
		xml += u'<reviews>' + u''.join([r.xml for r in model.SiteAlbumReview.gql('WHERE author = :1', user).fetch(1000)]) + u'</reviews>'
		self.sendXML(u'<my>' + xml + u'</my>')

	def get_albums(self, offset):
		return [star.album for star in SiteAlbumStar.gql('WHERE user = :1', self.force_user()).fetch(1000)]
