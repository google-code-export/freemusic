# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"""
Взаимодействие с профилем пользователя.
"""

from logging import debug as log

from google.appengine.api import users

import base
import mail
import model
import myxml
import invite

class List(base.BaseRequestHandler):
	xsltName = 'users.xsl'

	def get(self):
		self.check_access(admin=True)
		list = [user.to_xml() for user in model.SiteUser.all().fetch(1000)]
		self.sendXML(myxml.em(u'userlist', content=u''.join(list)))

	def post(self):
		self.check_access(admin=True)
		if self.request.get('invite'):
			for email in self.request.get_all('email'):
				user = model.SiteUser.gql('WHERE user = :1', users.User(email)).get()
				log(user)
				if user:
					user.invited = True
					user.put()
					mail.send(email, self.render('invitation.html', {
						'base': self.getBaseURL(),
						'nickname': user.user.nickname(),
						'email': email,
						'link': users.create_login_url(self.getBaseURL()),
					}))
		self.redirect('/users')

class ShowUser(base.BaseRequestHandler):
	"""
	Вывод профиля пользователя.
	"""
	xsltName = 'user.xsl'
	tabName = 'personal'

	def get(self, username):
		user = model.SiteUser.gql('WHERE user = :1', users.User(username + '@gmail.com')).get()
		if user is None:
			raise HTTPException(404, u'Нет такого пользователя.')
		xml = self.get_stars_xml(user)
		xml += self.get_reviews_xml(user)
		self.sendXML(user.to_xml(xml))

	def get_stars_xml(self, user):
		xml = u''
		for star in model.SiteAlbumStar.gql('WHERE user = :1', user.user).fetch(100):
			xml += myxml.em(u'star', {
				'album-id': star.album.id,
				'album-name': star.album.name,
				'artist-id': star.album.artist.id,
				'artist-name': star.album.artist.name,
				'pubDate': star.added.isoformat(),
			})
		return myxml.em(u'stars', content=xml)

	def get_reviews_xml(self, user):
		xml = u''
		for review in model.SiteAlbumReview.gql('WHERE author = :1', user).fetch(100):
			xml += myxml.em(u'review', {
				'album-id': review.album.id,
				'album-name': review.album.name,
				'artist-id': review.album.artist.id,
				'artist-name': review.album.artist.name,
				'pubDate': review.published,
				'average': review.rate_average,
			})
		return myxml.em(u'reviews', content=xml)

if __name__ == '__main__':
	base.run([
		('/u/([^/]+)$', ShowUser),
		('/users', List),
	])
