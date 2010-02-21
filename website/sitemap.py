# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

from google.appengine.ext import db

from model import SiteAlbum, SiteArtist
from base import BaseRequestHandler

class SitemapHandler(BaseRequestHandler):
	def get(self):
		content = '<?xml version="1.0" encoding="utf-8"?>\n'
		content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

		base = self.getBaseURL()

		"""
		for artist in SiteArtist.all().fetch(1000):
			content += "<url><loc>%sartist/%u</loc></url>\n" % (base, artist.id)
		"""

		for album in SiteAlbum.all().order('-id').fetch(1000):
			content += "<url><loc>%salbum/%u</loc></url>\n" % (base, album.id)

		content += "</urlset>"

		self.response.headers['Content-Type'] = 'text/xml'
		self.response.out.write(content)

class RobotsHandler(BaseRequestHandler):
	def get(self):
		content = "Sitemap: %ssitemap.xml\n" % self.getBaseURL()

		content += "User-agent: *\n"
		content += "Disallow: /static/\n"

		self.response.headers['Content-Type'] = 'text/plain'
		self.response.out.write(content)
