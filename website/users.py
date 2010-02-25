# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

from logging import debug as log

from google.appengine.api import users

from base import BaseRequestHandler
import mail
from model import SiteUser
import myxml
import invite

class List(BaseRequestHandler):
	xsltName = 'users.xsl'

	def get(self):
		self.check_access(admin=True)
		list = [user.to_xml() for user in SiteUser.all().fetch(1000)]
		self.sendXML(myxml.em(u'userlist', content=u''.join(list)))

	def post(self):
		self.check_access(admin=True)
		if self.request.get('invite'):
			for email in self.request.get_all('email'):
				user = SiteUser.gql('WHERE user = :1', users.User(email)).get()
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

class ShowUser(BaseRequestHandler):
	xsltName = 'user.xsl'

	def get(self, username):
		user = SiteUser.gql('WHERE user = :1', users.User(username + '@gmail.com')).get()
		if user is None:
			raise HTTPException(404, u'Нет такого пользователя.')
		self.sendXML(user.xml)
