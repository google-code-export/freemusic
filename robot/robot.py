#! /usr/bin/python
# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:
#
# TODO: отправлять имя пользователя, отправлять ему мыло

import getopt, sys, os
import urllib, urllib2
import base64, hmac, hashlib
import subprocess
import traceback
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

# local imports
from transcoder import Transcoder

try:
	import yaml
except:
	print "Please install python-yaml."
	sys.exit(1)

class Robot:
	def __init__(self, opts):
		self.verbose = False
		self.force = False
		self.password = ''
		self.host = None
		self.owner = None
		self.debug = False
		self.upload_dir = None

		config = yaml.load(self.readFile('$HOME/.config/freemusic.yaml'))
		if config:
			for k in config.keys():
				if hasattr(self, k):
					setattr(self, k, config[k])

	def uploadAlbum(self, xml):
		try:
			parseString(xml)
		except ExpatError, e:
			print "Invalid XML file:", e
			sys.exit(1)

		data = { 'xml': xml, 'signature': self.sign(xml) }
		if self.force:
			data['replace'] = 1
		self.post('upload/api', data)

	def post(self, url, data):
		if not self.host:
			raise Exception('host not set')
		url = 'http://' + self.host + '/' + url
		try:
			body = urllib.urlencode(data)
			if self.verbose:
				print "> uploading to %s: %s." % (url, body)
			req = urllib2.Request(url, body)
			response = urllib2.urlopen(req)
			self.showResponse(response.read())
		except urllib2.HTTPError, e:
			print str(e)

	def showResponse(self, response):
		xml = parseString(response)
		for em in xml.getElementsByTagName("response"):
			message = unicode(em.attributes["status"].value)
			if message == u"ok":
				message = u""
			try:
				extra = unicode(em.attributes["message"].value)
				if message:
					message += u": "
				message += extra
			except KeyError:
				pass
			print message
			return
		raise Exception("FAIL")

	def sign(self, data):
		dm = hmac.new(self.password, data, hashlib.sha1)
		return base64.b64encode(dm.digest())

	def readFile(self, filename):
		"""
		Возвращает содержимое указанного файла.  Если файла нет, возвращает пустую строку.
		"""
		filename = os.path.expandvars(filename)
		if os.path.exists(filename):
			f = open(filename, "r")
			data = f.read()
		else:
			print "no file: ", filename
			data = ""
		return data

	def processZipFile(self, filename):
		Transcoder(upload_dir=self.upload_dir).transcode(filename)

def usage():
	print "Usage: %s [options]" % (os.path.basename(sys.argv[0]))
	print "\nBasic options:"
	print " -a filename.xml  upload an album from this file"
	print " -f               force (overwrite existing albums, etc)"
	print " -h host          host name"
	print " -u filename      process and upload a zip file"
	print " -v               be verbose"
	return 2

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "a:dfh:p:u:v")
	except getopt.GetoptError, err:
		return usage()

	r = Robot(opts)
	for option, value in opts:
		if '-a' == option:
			f = open(value, 'r')
			r.uploadAlbum(f.read())
			f.close()
		if '-f' == option:
			r.force = True
		if '-h' == option:
			r.host = value
		if '-v' == option:
			r.verbose = True
		if '-p' == option:
			r.password = value
		if '-u' == option:
			r.processZipFile(value)

if __name__ == '__main__':
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		print "\rInterrupted."
	except Exception, e:
		print "\r%s: %s" % (e.__class__.__name__, str(e))
		traceback.print_exc()
	sys.exit(1)
