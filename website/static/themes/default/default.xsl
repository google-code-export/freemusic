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
				<title>Free Music Hub</title>
				<link rel="stylesheet" type="text/css" href="/static/themes/{@theme}/style.css"/>
				<link rel="shortcut icon" href="/static/favicon.2.ico"/>
				<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>
				<script type="text/javascript" src="/static/modernizr-1.1.min.js"></script>
				<script type="text/javascript" src="/static/scripts.js"></script>
				<link rel="alternate" type="application/rss+xml" title="RSS" href="/albums.rss"/> 
			</head>
			<body>
				<div id="wrapper">
					<div id="header">
						<form action="/search" method="get">
							<h1>
								<a href="/">
									<span>free music hub</span>
								</a>
							</h1>
							<input type="text" name="q" class="text"/>
							<input type="submit" value="Найти"/>
						</form>
					</div>
					<div id="content">
						<xsl:apply-templates select="*"/>
					</div>
					<div id="footer">
						<xsl:text>© ebm.net.ru - </xsl:text>
						<a href="/">Главная</a>
						<xsl:text> - </xsl:text>
						<a href="http://code.google.com/p/freemusic/" target="_blank">О проекте</a>
						<xsl:text> - </xsl:text>
						<a href="http://code.google.com/p/freemusic/issues/list" target="_blank">Поддержка</a>
						<xsl:if test="/page/@login-uri">
							<xsl:text> - </xsl:text>
							<a href="{/page/@login-uri}">Войти</a>
						</xsl:if>
						<xsl:if test="/page/@logout-uri">
							<xsl:text> - </xsl:text>
							<a href="{/page/@logout-uri}">Выйти</a>
							<xsl:if test="/page/@is-admin">
								<xsl:text> - </xsl:text>
								<a href="https://appengine.google.com/dashboard?app_id=free-music" target="_blank">Админка</a>
							</xsl:if>
						</xsl:if>
					</div>
				</div>
				<script type="text/javascript"><![CDATA[var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www."); document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E")); </script> <script type="text/javascript"> try { var pageTracker = _gat._getTracker("UA-12426390-1"); pageTracker._trackPageview(); } catch(err) {}]]></script>
			</body>
		</html>
	</xsl:template>

	<xsl:template match="/page[closed]">
		<html lang="{@lang}">
			<head>
				<title>Free Music Hub</title>
				<link rel="stylesheet" type="text/css" href="/static/style.css"/>
				<link rel="shortcut icon" href="/static/favicon.2.ico"/>
			</head>
			<body>
				<div id="closed">
					<xsl:choose>
						<xsl:when test="not(@login-uri)">
							<h2>Доступа пока нет</h2>
							<p>Вы получите приглашение как только придёт время.</p>
						</xsl:when>
						<xsl:otherwise>
							<h2>Мы ещё не открыты</h2>
							<p>Сайт находится на стадии закрытого тестирования. Вы можете оставить свой почтовый адрес, и мы пригласим вас к этому процессу, как только будем готовы.</p>
							<form method="post" action="/invite">
								<input type="text" name="email"/> <input type="submit" value="Отправить"/>
							</form>
							<p>Если у вас уже есть приглашение, можете <a href="{@login-uri}">войти</a>.</p>
						</xsl:otherwise>
					</xsl:choose>
				</div>
			</body>
		</html>
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

	<xsl:template name="lnav">
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
			<ul>
				<li><a href="/artists">Исполнители</a></li>
			</ul>
			<div class="uya">
				<p>Музыкант?</p>
				<a href="/upload">Загрузи свой альбом</a>
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
				<xsl:value-of select="@text" disable-output-escaping="yes"/>
			</p>
		</div>
	</xsl:template>

	<!-- additional stuff -->

	<xsl:template match="albums" mode="tiles">
		<ul class="altiles">
			<xsl:for-each select="album">
				<li class="album">
					<a href="/album/{@id}">
						<img width="100" height="100">
							<xsl:attribute name="src">
								<xsl:value-of select="images/image[@type='front']/@medium"/>
								<xsl:if test="not(images/image[@type='front'])">/static/cdaudio_mount.png</xsl:if>
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
				<img src="{@medium}" alt="image" width="100" height="100"/>
			</xsl:when>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="image" mode="medium">
		<xsl:choose>
			<xsl:when test="@medium">
				<a href="{@original}" target="_blank">
					<img src="{@medium}" width="200" height="200" alt="medium"/>
				</a>
			</xsl:when>
			<xsl:otherwise>
				<img src="/static/cdaudio_mount.png" width="200" height="200" alt="default image"/>
			</xsl:otherwise>
		</xsl:choose>
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
