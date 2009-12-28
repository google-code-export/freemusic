#! /usr/bin/python
# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:
#
# Функции для работы с обложками.

import Image

def find(files, outname='__folder.jpg'):
	extensions = ['jpg', 'jpeg', 'gif', 'png', 'bmp']
	for file in files:
		if file.split('.')[-1].lower() in extensions:
			img = Image.open(file)
			print "Using %s(%d×%d) for album art" % (file, img.size[0], img.size[1])
			if img.size[0] != img.size[1]:
				shift = (max(img.size) - min(img.size)) / 2
				print "Making it square."
				if img.size[0] > img.size[1]:
					crop = (shift, 0, shift + img.size[1], img.size[1])
				else:
					crop = (0, shift, img.size[0], shift + img.size[1])
				img = img.crop(crop)
				img.load()

			img.thumbnail((300, 300))
			img.save(outname, "JPEG")
			return outname
