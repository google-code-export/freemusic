# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import urllib
import urllib2
import sys
import xml.sax.saxutils as saxutils

# Different versions of ElementTree can exist in different locations depending
# on the installed Python version.
try:
	from xml.etree.cElementTree import *
except ImportError:
	try:
		from xml.etree.ElementTree import *
	except ImportError:
		from elementtree.ElementTree import *

def fetchxml(url, args=None):
	if type(args) == type({}):
		url += '?' + urllib.urlencode(args)
	return ElementTree(fromstring(fetch(url)))

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
