#! /usr/bin/python
# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:
#
# Функции для работы с обложками.

import logging, Image

def find(files, outname='__folder.jpg'):
	logging.info("Looking for album art")
	extensions = ['jpg', 'jpeg', 'gif', 'png', 'bmp']
	for file in files:
		if unicode(file).split('.')[-1].lower() in extensions:
			img = Image.open(unicode(file))
			logging.info("  found %s (%d×%d)" % (file, img.size[0], img.size[1]))
			if img.size[0] != img.size[1]:
				shift = (max(img.size) - min(img.size)) / 2
				logging.info("  making it square")
				if img.size[0] > img.size[1]:
					crop = (shift, 0, shift + img.size[1], img.size[1])
				else:
					crop = (0, shift, img.size[0], shift + img.size[1])
				img = img.crop(crop)
				img.load()
				logging.debug("    %d×%d" % (img.size[0], img.size[1]))

			img.thumbnail((300, 300))
			img.save(outname, "JPEG")
			return outname
	logging.info("  nothing")
