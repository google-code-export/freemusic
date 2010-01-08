# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:
#
# Примитивное журналирование.  Разнотипные сообщения записываются
# одновременно в файл и в stdout (если робот запущен без ключа -q).

file = None

def write(prefix, message):
	"Вывод строки.  Добавляет к каждой строке указанный префикс."
	global file
	text = prefix + u': ' + message
	print text
	if file is not None:
		file.write(text.encode('utf-8') + "\n")

def debug(message):
	"Вывод отладочного сообщения, с префиксом D."
	write(u'D', message)

def info(message):
	"Вывод информационного сообщения, с префиксом I."
	write(u'I', message)

def warning(message):
	"Вывод предупреждения об аномалии, с префиксом W."
	write(u'W', message)

def error(message):
	"Вывод сообщения об ошибке, с префиксом E."
	write(u'E', message)

def setfile(filename):
	"Открывает указанный файл, записывает BOM."
	global file
	file = open(filename, 'w', 1)
	file.write('\xef\xbb\xbf') # BOM, чтобы в винде можно было смотреть
	print "Logging to " + filename

def close():
	"Закрывает открытый файл."
	global file
	if file is not None:
		file.close()
		file = None
