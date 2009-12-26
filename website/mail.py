# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import re

from google.appengine.api import mail

def send(to, html):
	m = re.search('<h1>(.+)</h1>', html)
	if m:
		subject = m.group(1)
		html = html.replace(m.group(0), '').strip()
	else:
		subject = '(no subject)'
	# http://code.google.com/intl/ru/appengine/docs/python/mail/emailmessagefields.html
	mail.send_mail(sender='justin.forest@gmail.com', to=to, subject=subject, body=html, html=html)
