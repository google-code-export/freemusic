#! /usr/bin/python
# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 noet:

import logging, os

try:
	import mutagen.easyid3
	import mutagen.flac
	import mutagen.oggvorbis
except:
	print "Please install python-mutagen."
	sys.exit(1)

def get(filename):
	type = ext(filename)
	if type == 'flac':
		return mutagen.flac.FLAC(filename)

def set(filename, src):
	mode = ext(filename)
	if mode == 'mp3':
		dst = mutagen.easyid3.EasyID3()
		copy_tags(src, dst)
		dst.save(filename)
	elif mode == 'ogg':
		dst = mutagen.oggvorbis.OggVorbis(filename)
		copy_tags(src, dst)
		dst.save()
	elif mode == 'flac':
		dst = mutagen.flac.FLAC(filename)
		copy_tags(src, dst)
		dst.save()
	else:
		logging.info(filename + ': tags not supported')

def ext(filename):
	return filename.split('.')[-1].lower()

def copy_tags(src, dst):
	for tag in src:
		try:
			dst[tag] = src[tag]
			print " %s => %s" % (tag, dst[tag])
		except ValueError:
			pass
