# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

import re

def mksortname(name):
	name = unicode(name).lower()
	name = re.sub('[-_/\s.]+', ' ', name)
	name = re.sub(re.compile('[^\w\s]', re.U), u'', name)
	for prefix in (u'a', u'the'):
		if name.startswith(prefix + u' '):
			name = name[len(prefix)+1:] + u', ' + prefix
	return name
