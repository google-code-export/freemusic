# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

file = None

def write(prefix, message):
	global file
	text = prefix + u': ' + message
	print text
	if file is not None:
		file.write(text.encode('utf-8') + "\n")

def debug(message):
	write(u'D', message)

def info(message):
	write(u'I', message)

def warning(message):
	write(u'W', message)

def error(message):
	write(u'E', message)

def setfile(filename):
	global file
	file = open(filename, 'w', 1)
	print "Logging to " + filename

def close():
	global file
	if file is not None:
		file.close()
		file = None
