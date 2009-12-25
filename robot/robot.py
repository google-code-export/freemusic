#! /usr/bin/python
# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import getopt, sys, os
import urllib, urllib2
import base64, hmac, hashlib
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

__HOST__ = 'music.home.umonkey.net'

class Robot:
	url = 'http://music.home.umonkey.net/upload/api'

	def __init__(self, opts):
		self.verbose = False
		self.force = False
		self.password = ''

	def uploadAlbum(self, xml):
		try:
			parseString(xml)
		except ExpatError, e:
			print "Invalid XML file:", e
			sys.exit(1)

		data = { 'xml': xml, 'signature': self.sign(xml) }
		if self.force:
			data['replace'] = 1
		self.post(self.url, data)

	def post(self, url, data):
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
			message = em.attributes["status"].value
			if message == "ok":
				message = ""
			try:
				extra = em.attributes["message"].value
				if message:
					message += ": "
				message += extra
			except KeyError:
				pass
			print message
			return
		raise Exception("FAIL")

	def sign(self, data):
		dm = hmac.new(self.password, data, hashlib.sha1)
		return base64.b64encode(dm.digest())

def usage():
	print "Usage: %s [options]" % (os.path.basename(sys.argv[0]))
	print "\nBasic options:"
	print " -a filename.xml  upload an album from this file"
	print " -f               force (overwrite existing albums, etc)"
	print " -h host          host name, defaults to %s" % __HOST__
	print " -v               be verbose"
	return 2

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "a:fh:v")
	except getopt.GetoptError, err:
		return usage()

	r = Robot(opts)
	for option, value in opts:
		if '-a' == option:
			f = open(value, 'r')
			r.uploadAlbum(f.read())
			f.close()
		if '-v' == option:
			r.verbose = True
		if '-f' == option:
			r.force = True

if __name__ == '__main__':
	sys.exit(main())
