<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output
		omit-xml-declaration="yes"
		version="1.0"
		encoding="utf-8"
		indent="yes"
		method="html"
		doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"
		doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
		/>

	<xsl:variable name="index-image-type">thumbnail</xsl:variable><!-- thumbnail, medium -->

	<xsl:template match="/page">
		<html lang="{@lang}">
			<head>
				<title>music 3.5</title>
				<link rel="stylesheet" type="text/css" href="/static/style.css"/>
				<link rel="shortcut icon" href="/static/favicon.2.ico"/>
				<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>
				<script type="text/javascript" src="/static/scripts.js"></script>
				<link rel="alternate" type="application/rss+xml" title="RSS" href="/albums.rss"/> 
			</head>
			<body>
				<div id="wrapper">
					<div id="header">
						<form action="/search" method="get">
							<h1>
								<a href="/">new music</a>
							</h1>
							<input type="text" name="q" class="text"/>
							<input type="submit" value="Найти"/>
						</form>
					</div>
					<xsl:apply-templates select="*"/>
					<div id="footer">
						<xsl:text>© ebm.net.ru - </xsl:text>
						<a href="/">Главная</a>
						<xsl:text> - </xsl:text>
						<a href="http://code.google.com/p/freemusic/">О проекте</a>
						<xsl:if test="/page/@login-uri">
							<xsl:text> - </xsl:text>
							<a href="{/page/@login-uri}">Войти</a>
						</xsl:if>
						<xsl:if test="/page/@logout-uri">
							<xsl:text> - </xsl:text>
							<a href="{/page/@logout-uri}">Выйти</a>
							<xsl:text> - </xsl:text>
							<a href="/_ah/admin">Админка</a>
						</xsl:if>
					</div>
				</div>
			</body>
		</html>
	</xsl:template>

	<xsl:template match="/page/album">
		<div id="album">
			<xsl:apply-templates select="." mode="h2"/>
			<div class="left">
				<xsl:apply-templates select="images/image[position()=1]" mode="medium"/>
				<ul>
					<li>
						<a href="{files/file/@uri}">Скачать альбом</a>
					</li>
					<xsl:if test="/page/@user = @owner or /page/@is-admin">
						<li>
							<a href="/album/{@id}/edit">Отредактировать</a>
						</li>
					</xsl:if>
				</ul>
				<xsl:apply-templates select="labels" mode="linked">
					<xsl:with-param name="uri">/?label=</xsl:with-param>
				</xsl:apply-templates>
			</div>
			<div class="right">
				<table>
					<tbody>
						<xsl:for-each select="tracks/track">
							<tr>
								<td class="r">
									<xsl:value-of select="position()"/>
									<xsl:text>.</xsl:text>
								</td>
								<td>
									<a href="/track/{@id}">
										<xsl:value-of select="@title"/>
									</a>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<xsl:if test="@pubDate">
					<p>Выпущен <xsl:value-of select="concat(substring(@pubDate,9,2),'.',substring(@pubDate,6,2),'.',substring(@pubDate,1,4))"/></p>
				</xsl:if>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="/page/form/album">
		<div class="twocol">
			<div class="right">
				<xsl:apply-templates select="." mode="h2"/>
				<form method="post" class="gen eal">
					<div>
						<label>
							<span>Заголовок:</span>
							<input type="text" class="text" name="name" value="{@name}"/>
						</label>
					</div>
					<div>
						<label>
							<span>Дата публикации:</span>
							<input type="text" class="text" name="pubDate" value="{@pubDate}"/>
						</label>
					</div>
					<div>
						<label>
							<span>Описание:</span>
							<textarea class="text" name="text">
								<xsl:value-of select="@text"/>
							</textarea>
						</label>
					</div>
					<div>
						<label>
							<span>Метки:</span>
							<input type="text" class="text" name="labels">
								<xsl:attribute name="value">
									<xsl:for-each select="labels/label">
										<xsl:value-of select="text()"/>
										<xsl:if test="position()!=last()">
											<xsl:text>, </xsl:text>
										</xsl:if>
									</xsl:for-each>
								</xsl:attribute>
							</input>
						</label>
					</div>
					<fieldset>
						<legend>Названия дорожек:</legend>
						<ol>
							<xsl:for-each select="tracks/track">
								<li>
									<input type="text" class="text" name="track.{position()}" value="{@title}"/>
								</li>
							</xsl:for-each>
						</ol>
					</fieldset>
					<div>
						<input type="submit" value="Сохранить изменения"/> или <a href="/album/{@id}">вернуться без сохранения</a>
					</div>
				</form>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="/page/track">
		<div class="twocol">
			<div class="right">
				<h2>
					<xsl:value-of select="@title"/>
				</h2>
				<p>Из альбома <a href="/album/{@album-id}"><xsl:value-of select="@album-name"/></a>.</p>
				<xsl:if test="@mp3-link or @ogg-link">
					<audio controls="controls">
						<xsl:if test="@mp3-link">
							<source src="{@mp3-link}" type="audio/mp3"/>
						</xsl:if>
						<xsl:if test="@ogg-link">
							<source src="{@ogg-link}" type="audio/ogg; codecs=vorbis"/>
						</xsl:if>
					</audio>
				</xsl:if>
				<ul>
					<xsl:if test="@mp3-link">
						<li>
							<a href="{@mp3-link}">Скачать MP3</a>
						</li>
					</xsl:if>
					<xsl:if test="@ogg-link">
						<li>
							<a href="{@ogg-link}">Скачать OGG/Vorbis</a>
						</li>
					</xsl:if>
				</ul>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="album" mode="h2">
		<h2>
			<xsl:text>«</xsl:text>
			<xsl:value-of select="@name"/>
			<xsl:text>»</xsl:text>
			<small>
				<xsl:text> от </xsl:text>
				<a href="/artist/{@artist-id}">
					<xsl:value-of select="@artist-name"/>
				</a>
			</small>
		</h2>
	</xsl:template>

	<xsl:template match="files">
		<h3><a href="{file/@uri}">Download</a></h3>
		<ul>
			<xsl:for-each select="file">
				<li>
					<a href="{@uri}">
						<xsl:value-of select="@name"/>
					</a>
				</li>
			</xsl:for-each>
		</ul>
	</xsl:template>

	<xsl:template match="/page/upload">
		<div id="aupload">
			<h2>Загрузка альбома</h2>
			<form action="http://{@worker}">
				<div>
					<input type="file" name="file"/>
				</div>
				<input type="submit"/>
			</form>
		</div>
	</xsl:template>

	<xsl:template match="upload-xml-form">
		<h2>Upload XML</h2>
		<form method="post" enctype="multipart/form-data">
			<div>
				<input type="file" name="xml"/>
			</div>
			<input type="submit"/>
		</form>
	</xsl:template>

	<xsl:template match="/page/upload-remote">
		<div class="onecol">
			<h2>Загрузка альбома с другого сайта</h2>
			<form method="post" class="gen">
				<div>
					<label>
						<span>Адрес ZIP-архива:</span>
						<input type="text" name="url" class="text"/>
					</label>
					<p class="hint">Это должна быть прямая ссылка, страницы-посредники вроде RapidShare работать не будут.</p>
				</div>
				<input type="submit"/>
			</form>
		</div>
	</xsl:template>

	<xsl:template match="/page/index">
		<div id="index" class="twocol">
			<div class="left">
				<ul>
					<li><a href="/">Свежие</a></li>
					<li><a href="/">Популярные</a></li>
					<li><a href="/">Рекомендуемые</a></li>
					<xsl:if test="../@label">
						<li>
							<xsl:value-of select="concat('С меткой «',../@label,'»')"/>
						</li>
					</xsl:if>
				</ul>
				<div class="uya">
					<p>Музыкант?</p>
					<a href="/upload">Загрузи свой альбом</a>
				</div>
			</div>
			<div class="right">
				<xsl:apply-templates select="albums" mode="tiles"/>
				<ul class="pager">
					<xsl:if test="@skip &gt; 14">
						<li>
							<a href="?skip={@skip - 15}">« Назад</a>
						</li>
					</xsl:if>
					<xsl:if test="count(albums/album) = 15">
						<!-- TODO: аяксовая подгрузка ещё 15 альбомов сюда же -->
						<li>
							<a href="?skip={@skip + 15}">Ещё »</a>
						</li>
					</xsl:if>
				</ul>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="/page/artist">
		<div class="twocol">
			<div class="left">
			</div>
			<div class="right">
				<h2>
					<xsl:value-of select="@name"/>
				</h2>
				<xsl:apply-templates select="albums" mode="tiles"/>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="/page/message">
		<div class="onecol">
			<h2>
				<xsl:value-of select="@title"/>
				<xsl:if test="not(@title)">
					<xsl:text>Ошибка</xsl:text>
				</xsl:if>
			</h2>
			<p>
				<xsl:value-of select="@text"/>
			</p>
		</div>
	</xsl:template>

	<xsl:template match="/page/queue">
		<h2>Очередь обработки <small><a href="/api/queue.yaml">yaml</a></small></h2>
		<xsl:if test="file">
			<ul>
				<xsl:for-each select="file">
					<xsl:sort select="@id" data-type="number"/>
					<li>
						<xsl:value-of select="@id"/>
						<xsl:text>. </xsl:text>
						<tt>
							<a href="{@uri}">
								<xsl:value-of select="@name"/>
							</a>
						</tt>
						<xsl:if test="@owner">
							<small>
								<xsl:text> от </xsl:text>
								<xsl:value-of select="@owner"/>
							</small>
						</xsl:if>
						<xsl:if test="/page/@is-admin">
							<xsl:text> </xsl:text>
							<small>
								<a href="/api/queue/delete?id={@id}">×</a>
							</small>
						</xsl:if>
					</li>
				</xsl:for-each>
			</ul>
		</xsl:if>
		<xsl:if test="not(file)">
			<p>Очередь пуста, <a href="/upload">загрузи</a> что-нибудь<a href="/upload/remote">!</a></p>
		</xsl:if>
	</xsl:template>

	<!-- additional stuff -->

	<xsl:template match="albums" mode="tiles">
		<ul class="altiles">
			<xsl:for-each select="album">
				<li class="album">
					<a href="/album/{@id}">
						<img width="100" height="100">
							<xsl:attribute name="src">
								<xsl:value-of select="images/image[position()=1]/@small"/>
								<xsl:if test="not(images/image[position()=1]/@small)">/static/cdaudio_mount.png</xsl:if>
							</xsl:attribute>
						</img>
					</a>
					<div>
						<a class="n" href="/album/{@id}">
							<xsl:value-of select="@name"/>
						</a>
						<small>
							<xsl:text> by </xsl:text>
							<a href="/artist/{@artist-id}">
								<xsl:value-of select="@artist-name"/>
							</a>
						</small>
					</div>
				</li>
			</xsl:for-each>
		</ul>
	</xsl:template>

	<xsl:template match="image">
		<xsl:param name="size">medium</xsl:param>
		<xsl:choose>
			<xsl:when test="$size='medium'">
				<img src="{@medium}" alt="image" width="200" height="200"/>
			</xsl:when>
			<xsl:when test="$size='small'">
				<img src="{@small}" alt="image" width="100" height="100"/>
			</xsl:when>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="image" mode="medium">
		<xsl:choose>
			<xsl:when test="@medium">
				<a href="{@original}">
					<img src="{@medium}" width="200" height="200" alt="medium"/>
				</a>
			</xsl:when>
			<xsl:otherwise>
				<img src="/static/cdaudio_mount.png" width="200" height="200" alt="default image"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="s3-settings">
		<h2>Amazon S3 Settings</h2>
		<form action="{@action}" method="post" class="gen">
			<div>
				<label for="s3a">Access Key:</label>
				<input id="s3a" type="text" name="s3a" value="{@s3a}" class="text"/>
			</div>
			<div>
				<label for="s3s">Secret Key:</label>
				<input id="s3s" type="text" name="s3s" value="{@s3s}" class="text"/>
			</div>
			<div>
				<label for="bucket">Bucket Name:</label>
				<input id="bucket" type="text" name="bucket" value="{@bucket}" class="text"/>
			</div>
			<!--
			<div>
				<label for="after">После загрузки переходить на:</label>
				<input id="after" type="text" name="after" value="{@after}" class="text"/>
			</div>
			-->
			<div>
				<input type="submit" value="Save" class="button"/>
			</div>
		</form>
	</xsl:template>

	<xsl:template match="s3-upload-form">
		<div class="twocol">
			<!--
			<div class="left">
				<ul>
					<li><a href="/upload">Обычная загрузка</a></li>
					<li><a href="/upload/ftp">Загрузка по FTP</a></li>
				</ul>
			</div>
			-->
			<div class="right">
				<h2>Загрузка нового альбома</h2>
				<!--
				http://docs.amazonwebservices.com/AmazonS3/2006-03-01/index.html?UsingHTTPPOST.html
				-->
				<p>Пожалуйста, подготовьте ZIP архив со всеми звуковыми файлами, картинками, буклетами и всем, что считаете нужным.&#160; Чем лучшего качества будут звуковые файлы, тем лучше; мы рекомендуем <a href="http://ru.wikipedia.org/wiki/FLAC" target="_blank">FLAC</a>, WAV или AIFF (мы сами сделаем из них MP3 и OGG).</p>
				<p>После загрузки файла наши роботы примутся его обрабатывать, о результатах вам сообщат по электронной почте.</p>
				<p>И будет здорово, если ваш браузер умеет показывать ход загрузки.&#160; Мы рекомендуем <a href="http://www.google.com/chrome/" target="_blank">Google Chrome</a>.</p>
				<label><input type="checkbox" class="toggle"/> Всё понятно</label>
				<form action="http://{@bucket}.s3-external-3.amazonaws.com/" method="post" enctype="multipart/form-data" class="hidden toggleMe fileUpload">
					<input type="hidden" name="AWSAccessKeyId" value="{@access-key}"/>
					<input type="hidden" name="acl" value="public-read"/>
					<input type="hidden" name="key" value="{@key}"/>
					<input type="hidden" name="policy" value="{@policy}"/>
					<input type="hidden" name="signature" value="{@signature}"/>
					<input type="hidden" name="success_action_redirect" value="{@base}upload"/>
					<div>
						<input type="file" name="file"/>
					</div>
					<div>
						<input type="submit" value="Начать загрузку"/>
					</div>
				</form>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="s3-upload-ok">
		<div class="twocol">
			<div class="right">
				<h2>Загрузка завершена</h2>
				<p>Файл успешно загружен, ему присвоен <a href="/api/queue.xml#{@file-id}">номер <xsl:value-of select="@file-id"/></a>.&#160; Наши роботы скоро им займутся, обо всём происходящем вам будут сообщать по электронной почте.</p>
				<p><a href="/upload">Загрузить ещё один файл</a></p>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="s3-login-message">
		<div class="twocol">
			<div class="right">
				<h2>Загрузка нового альбома</h2>
				<p>Для этого вам понадобится авторизоваться.&#160; Если вы ещё не&#160;зарегистрированы в&#160;Google, вы можете без&#160;труда сделать это.</p>
				<p><a href="{/page/@login-uri}">Продолжить</a></p>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="labels" mode="linked">
		<xsl:param name="uri"/>
		<ul class="labels">
			<xsl:for-each select="label">
				<xsl:sort select="text()"/>
				<li>
					<a href="{$uri}{@uri}">
						<xsl:value-of select="text()"/>
					</a>
				</li>
			</xsl:for-each>
		</ul>
	</xsl:template>
</xsl:stylesheet>
