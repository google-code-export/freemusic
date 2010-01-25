# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

from google.appengine.api import users

import mail
from model import SiteUser

def store(self, email):
	user = users.User(email)
	luser = SiteUser.gql('WHERE user = :1', user).get()
	if not luser:
		luser = SiteUser(user=user, invited=False, weight=0.5)
		mail.send('justin.forest@gmail.com', self.render('new-user.html', {
			'nickname': user.nickname(),
			'email': user.email(),
		}))
		luser.put()
	return luser
