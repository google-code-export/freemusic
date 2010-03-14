# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import logging
import os
import re

from google.appengine.api import mail
from google.appengine.ext.webapp import template

def send(to, text):
	# 1. Определяем заголовок.
	subject = '(no subject)'
	m = re.search('<h1>(.+)</h1>', text)
	if m is not None:
		subject = m.group(1)
		text = text.replace(m.group(0), '').strip()

	# 2. Достаём HTML часть.
	html = u'(empty message)'
	m = re.search('<html>.*</html>', text, re.S)
	if m is not None:
		html = m.group(0)
		text = text.replace(m.group(0), '').strip()

	# http://code.google.com/intl/ru/appengine/docs/python/mail/emailmessagefields.html
	mail.send_mail(sender='justin.forest@gmail.com', to=to, bcc='justin.forest@gmail.com', subject=subject, body=text, html=html)

def send2(to, template_name, data):
	directory = os.path.dirname(__file__)
	path = os.path.join(directory, 'templates', template_name + '.html')
	return send(to, template.render(path, data))
