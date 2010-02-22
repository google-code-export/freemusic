# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import base

class ShowRadio(base.BaseRequestHandler):
	xsltName = 'radio.xsl'

	def get(self):
		self.sendXML(u'<radio/>')
