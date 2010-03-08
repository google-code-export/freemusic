# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"""
Вывод главной страницы настроек.
"""

import base

class SettingsPage(base.BaseRequestHandler):
	xsltName = 'settings.xsl'

	def get(self):
		self.force_admin()
		self.sendXML(u'<settings/>')
