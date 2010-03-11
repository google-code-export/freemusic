# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import base64
import hmac
import hashlib
import os
import subprocess
import sys
import tempfile
import urllib
import urllib2

import settings

def fetch(url, data=None):
	"""
	Запрашивает указанный URL, возвращает результат.  Если указан параметр data,
	его содержимое отправляется методом POST (обычно это словарь).
	"""
	try:
		if data is not None:
			data = urllib.urlencode(data)
		u = urllib2.urlopen(urllib2.Request(url.encode('utf-8'), data))
		if u is not None:
			return u.read()
	except urllib2.HTTPError, e:
		print >>sys.stderr, 'Error fetching %s: %s' % (url, e)

def download(url):
	def progress(a, b, c):
		print 'Progress: %u/%u kB\r' % (a*b/1024, c/1024),
	print 'Downloading', url
	a = urllib.urlretrieve(url, None, progress)
	print 'File saved as', a[0]
	return a[0]

def sign(data):
	dm = hmac.new(settings.settings['password'], data, hashlib.sha1)
	return base64.b64encode(dm.digest())

def mail(to, subject, body):
	"Отправка почты."
	# from http://www.yak.net/fqa/84.html
	p = os.popen('/usr/sbin/sendmail -t', 'w')
	p.write('To: %s\nSubject: %s\n\n' % (to, subject))
	p.write(body)
	sts = p.close()
	if sts:
		raise Exception('Could not send mail (status=%s).' % sts)

def pipe(commands, logger=None):
	def mylogger(msg):
		print msg
	if logger is None:
		logger = mylogger
	logger(u'! ' + u' |\n  '.join([u' '.join(command) for command in commands]))
	clist = [] # на всякий случай, чтобы деструкторов не было
	stdin = None
	for command in commands:
		clist.append(subprocess.Popen(command, stdout=subprocess.PIPE, stdin=stdin))
		stdin = clist[-1].stdout
	response = clist[-1].communicate()
	if clist[-1].returncode:
		logger('%d: %s' % (clist[-1].returncode, response))
		raise Exception(response[1])
	return response[0]

def upload(folder):
	"""
	Загружает содержимое папки в S3, возвращает URL загруженной папки.
	"""
	if not settings.settings['s3path']:
		raise Exception('s3path not set, unable to upload.')
	if not os.path.isdir(folder):
		raise Exception('util.upload expects a folder path.')
	pipe([[ 's3cmd', 'sync', '-PMHr', folder, settings.settings['s3path'] ]])
	return settings.settings['s3base'] + os.path.split(folder)[-1]
