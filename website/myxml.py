# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import urllib
import xml.sax.saxutils as saxutils

def em(emname, attrs=None, content=None, empty=True):
	if not empty and not content:
		return u''
	xml = u'<' + emname
	if attrs is not None:
		for k in attrs:
			value = attrs[k]
			if value:
				if True == value and type(value) == type(True):
					value = u'yes'
				else:
					value = unicode(value)
				xml += u' ' + k + u'=' + escape(value)
	if content:
	   xml += u'>' + content + u'</' + emname + u'>'
	else:
		xml += u'/>'
	return xml

def uri(value):
	return urllib.quote(unicode(value).encode('utf-8'))

def escape(value):
	if type(value) == type(str()) or type(value) == type(unicode()):
		value = saxutils.quoteattr(value)
	return value

def cdata(value):
	if type(value) == type(str()) or type(value) == type(unicode()):
		value = u'<![CDATA[' + unicode(value) + ']]>'
	return value
