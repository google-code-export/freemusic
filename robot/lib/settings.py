# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:
#
# Интерфейс к настройкам.  Читает содержимое файла ~/.config/freemusic.yaml,
# может быть изменено на лету.

import os, sys

data = {}

try:
	import yaml
except:
	print "Please install python-yaml."
	sys.exit(1)

class settings:
	def __init__(self):
		self.data = {}
		self.load()

	def load(self):
		filename = os.path.expandvars('$HOME/.config/freemusic.yaml')
		if os.path.exists(filename):
			self.data = yaml.load(open(filename, 'r').read().decode('utf-8'))

	def save(self):
		pass

	def __getitem__(self, key):
		if key in self.data:
			return self.data[key]
		return None

	def __setitem__(self, key, value):
		self.data[key] = value

	def list(self, key):
		if key not in self.data:
			return []
		elif type(self.data[key]) != type([]):
			return [self.data[key]]
		else:
			return self.data[key]

	def validate(self):
		for k in ('host', 'upload_dir'):
			if k not in self.data:
				raise Exception(u'%s not set, use either ~/.config/freemusic.yaml, or run me with -d %s=xyz' % (k, k))

settings = settings()
