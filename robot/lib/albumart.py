#! /usr/bin/python
# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:
#
# Функции для работы с обложками.

import Image
import os

import logger

def find(files, outname=u'__folder.jpg'):
	logger.info(u"Looking for album art")
	extensions = [u'jpg', u'jpeg', u'gif', u'png', u'bmp']
	for file in files:
		if str(file.split('.')[-1].lower()) in extensions:
			logger.info(u'Using ' + file)
			return resize(file, 300)
	logger.info(u"  nothing")

def resize(filename, width):
	img = Image.open(unicode(filename))
	if img.mode != 'RGB':
		img = img.convert('RGB')
	if img.size[0] != img.size[1]:
		shift = (max(img.size) - min(img.size)) / 2
		if img.size[0] > img.size[1]:
			crop = (shift, 0, shift + img.size[1], img.size[1])
		else:
			crop = (0, shift, img.size[0], shift + img.size[1])
		img = img.crop(crop)
		img.load()

	outname = os.path.splitext(filename)[0] + u'.' + str(width) + u'x' + str(width) + u'.jpg'
	img.thumbnail((width, width))
	img.resize((width, width), Image.BICUBIC).save(outname, 'JPEG')
	# img.save(outname, "JPEG")
	return outname
