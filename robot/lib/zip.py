# vim: set ts=4 sts=4 sw=4 noet fileencoding=utf-8:

"Функции для работы с ZIP архивами."

import logger
import os
import zipfile

def unzip(zipname, tmpdir):
	"""
	Распаковывает указанный ZIP архив во временную папку,
	возвращает список с именами файлов.
	"""
	logger.info("unzipping " + zipname)
	result = []
	try:
		zip = zipfile.ZipFile(zipname)
	except zipfile.BadZipfile, e:
		logger.error(str(e))
		return []
	for f in sorted(zip.namelist()):
		if not f.endswith('/'):
			name = os.path.basename(f)
			try:
				name = name.decode('utf-8')
			except UnicodeDecodeError:
				parts = os.path.splitext(name)
				name = urllib.quote(parts[0]).replace('%', 'x') + parts[1]
			if name.startswith('.'):
				logger.debug(u'- ' + name)
			else:
				result.append(os.path.join(unicode(tmpdir), name))
				out = open(result[-1], 'wb')
				out.write(zip.read(f))
				out.close()
				logger.info(u"< " + name)
	return result

def zip(filename, files):
	logger.info(u'creating ' + filename)
	z = zipfile.ZipFile(filename, 'w')
	for file in files:
		if not file.endswith('.zip'):
			logger.info(u"+ " + file)
			z.write(file, os.path.basename(file))
	z.close()
	return filename
