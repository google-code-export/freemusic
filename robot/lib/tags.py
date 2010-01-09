# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"""
Функции для работы с тэгами.
http://code.google.com/p/mutagen/wiki/Tutorial
"""

import base64
import datetime
import os
import re
import sys

import logger

try:
	import mutagen.easyid3
	import mutagen.id3
	import mutagen.flac
	import mutagen.mp3
	import mutagen.oggvorbis
except:
	print "Please install python-mutagen."
	sys.exit(1)

__all__ = [ "get", "set" ]

def get(filename):
	type = ext(filename)
	try:
		if type == 'flac':
			return mutagen.flac.Open(filename)
		elif type == 'mp3':
			return mutagen.easyid3.Open(filename)
		elif type == 'ogg':
			return mutagen.oggvorbis.Open(filename)
	except Exception, e:
		logger.warning('%s: %s' % (e.__class__.__name__, str(e)))
		tags = { 'title': os.path.basename(filename) }
		x = re.match('(\d+)', tags['title'])
		if x:
			tags['tracknumber'] = x.group(1)
		return tags

def set(filename, src, cover=None):
	mode = ext(filename)
	if mode == 'mp3':
		dst = mutagen.easyid3.EasyID3()
		copy_tags(src, dst)
		dst.save(filename)
		if cover:
			id3 = mutagen.mp3.MP3(filename)
			id3.tags.add(mutagen.id3.APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=open(cover).read()))
			id3.save()
	elif mode == 'ogg':
		dst = mutagen.oggvorbis.OggVorbis(filename)
		copy_tags(src, dst)
		if cover:
			dst['COVERARTMIME'] = u'image/jpeg'
			dst['COVERARTTYPE'] = u'3'
			dst['COVERARTDESCRIPTION'] = u'Cover'
			dst['COVERART'] = unicode(base64.b64encode(open(cover).read()))
		dst.save()
	elif mode == 'flac':
		dst = mutagen.flac.FLAC(filename)
		copy_tags(src, dst)
		dst.save()
	else:
		logger.info(filename + ': tags not supported')

def ext(filename):
	return filename.split('.')[-1].lower()

def copy_tags(src, dst):
	for tag in sorted(src):
		try:
			dst[tag] = src[tag]
		except ValueError:
			logger.warning('Error settings tag ' + tag)
			pass

def duration(filename):
	type = ext(filename)
	if type == 'flac':
		return mutagen.flac.Open(filename).info.length
	elif type == 'ogg':
		return mutagen.oggvorbis.Open(filename).info.length
	elif type == 'mp3':
		return mutagen.mp3.Open(filename).info.length
