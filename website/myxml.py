# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import urllib
from xml.sax.saxutils import escape

def em(emname, attrs=None, content=None, empty=True):
	if not empty and not content:
		return u''
	xml = u'<' + emname
	if attrs is not None:
		for k in attrs:
			value = attrs[k]
			if value:
				if type(value) == type(str()) or type(value) == type(unicode()):
					value = escape(value)
				elif True == value:
					value = u'yes'
				else:
					value = unicode(value)
				xml += u' ' + k + u'="' + value + u'"'
	if content:
	   xml += u'>' + content + u'</' + emname + u'>'
	else:
		xml += u'/>'
	return xml

def uri(value):
	return urllib.quote(unicode(value).encode('utf-8'))
