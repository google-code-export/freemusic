#! /usr/bin/python
# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:
#
# Функции для работы с обложками.

import Image, logging, os

def find(files, outname='__folder.jpg'):
	logging.info("Looking for album art")
	extensions = ['jpg', 'jpeg', 'gif', 'png', 'bmp']
	for file in files:
		if unicode(file).split('.')[-1].lower() in extensions:
			return resize(unicode(file), 300)
	logging.info("  nothing")

def resize(filename, width):
	img = Image.open(unicode(filename))
	if img.size[0] != img.size[1]:
		shift = (max(img.size) - min(img.size)) / 2
		if img.size[0] > img.size[1]:
			crop = (shift, 0, shift + img.size[1], img.size[1])
		else:
			crop = (0, shift, img.size[0], shift + img.size[1])
		img = img.crop(crop)
		img.load()

	outname = os.path.splitext(filename)[0] + '.' + str(width) + 'x' + str(width) + '.jpg'
	img.thumbnail((width, width))
	img.resize((width, width), Image.BICUBIC).save(outname, 'JPEG')
	# img.save(outname, "JPEG")
	return outname
