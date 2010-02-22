# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import re
import urllib

# Different versions of ElementTree can exist in different locations depending
# on the installed Python version.
try:
	from xml.etree.cElementTree import *
except ImportError:
	try:
		from xml.etree.ElementTree import *
	except ImportError:
		from elementtree.ElementTree import *

from google.appengine.api import urlfetch

def mksortname(name):
	name = unicode(name).lower()
	name = re.sub('[-_/\s.]+', ' ', name)
	name = re.sub(re.compile('[^\w\s]', re.U), u'', name)
	for prefix in (u'a', u'the'):
		if name.startswith(prefix + u' '):
			name = name[len(prefix)+1:] + u', ' + prefix
	return name

def fetchxml(url, args=None):
	if type(args) == type({}):
		url += '?' + urllib.urlencode(args)
	result = urlfetch.fetch(url)
	if result.status_code == 200:
		return ElementTree(fromstring(result.content))

def to_xml(et):
	return tostring(et)
