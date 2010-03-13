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
				<link rel="stylesheet" type="text/css" href="/static/player.css"/>
				<link rel="shortcut icon" href="/static/favicon.2.ico"/>
				<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>
				<script type="text/javascript" src="/static/modernizr-1.1.min.js"></script>
				<script type="text/javascript" src="/static/player.js"></script>
				<script type="text/javascript" src="/static/scripts.js"></script>
				<link rel="alternate" type="application/rss+xml" title="RSS" href="/albums.rss"/> 
				<meta name="google-site-verification" content="1YzbBazX2CGFQgRb0kDx_Y8rqw4oOfS_g3rVC6faZP8"/>
			</head>
			<body>
				<div id="header">
					<div class="corsette">
						<h1>
							<a href="/" class="wbg">
								<span>Free Music Hub</span>
							</a>
						</h1>
						<ul class="menu">
							<li>
								<xsl:attribute name="class">
									<xsl:text>wsub</xsl:text>
									<xsl:if test="/page/@tab='music'">
										<xsl:text> active</xsl:text>
									</xsl:if>
								</xsl:attribute>
								<a href="/">Музыка</a>
								<ul class="submenu">
									<li>
										<a href="/artists">Исполнители</a>
									</li>
									<li>
										<a href="/reviews">Рецензии</a>
									</li>
									<!--
									<li>
										<a href="/chart">Рейтинг</a>
									</li>
									-->
									<li>
										<a href="/player">Проигрыватель</a>
									</li>
									<li>
										<a href="/radio">Радио</a>
									</li>
								</ul>
							</li>
							<li>
								<xsl:if test="/page/@tab='events'">
									<xsl:attribute name="class">active</xsl:attribute>
								</xsl:if>
								<a href="/events">Афиша</a>
							</li>
							<li>
								<xsl:if test="/page/@tab='chart'">
									<xsl:attribute name="class">active</xsl:attribute>
								</xsl:if>
								<a href="/chart">Рейтинг</a>
							</li>
							<xsl:if test="/page/@logout-uri">
								<li class="wsub">
									<xsl:if test="/page/@tab='personal'">
										<xsl:attribute name="class">active</xsl:attribute>
									</xsl:if>
									<a href="/u/{/page/@user}">
										<xsl:value-of select="/page/@user"/>
									</a>
									<ul class="submenu">
										<li>
											<a href="/player?user={/page/@user}">Коллекция</a>
										</li>
										<li>
											<a href="/upload">Загрузить альбом</a>
										</li>
										<xsl:if test="/page/@is-admin">
											<li>
												<a class="ext">
													<xsl:attribute name="href">
														<xsl:choose>
															<xsl:when test="contains(/page/@logout-uri,'dev.freemusichub.net')">/_ah/admin</xsl:when>
															<xsl:otherwise>https://appengine.google.com/dashboard?app_id=free-music</xsl:otherwise>
														</xsl:choose>
													</xsl:attribute>
													<xsl:text>Админка</xsl:text>
												</a>
											</li>
											<li>
												<a href="/settings">Настройка сайта</a>
											</li>
										</xsl:if>
										<li>
											<a href="{/page/@logout-uri}">Выйти</a>
										</li>
									</ul>
								</li>
							</xsl:if>
							<xsl:if test="/page/@login-uri">
								<li>
									<a href="{/page/@login-uri}">Войти</a>
								</li>
							</xsl:if>
						</ul>
						<form action="/search" method="get" class="search">
							<input type="text" name="q" class="text clearme" value="Поиск по сайту"/>
							<button type="submit">
								<span>Найти</span>
							</button>
						</form>
					</div>
				</div>
				<div id="wrapper">
					<div id="content">
						<div id="plh">
							<p>Вы можете использовать метки для поиска интересующей музыки:</p>
						</div>
						<div id="ntfctn"></div>
						<xsl:apply-templates select="*"/>
					</div>
					<div id="footer">
						<xsl:text>© ebm.net.ru - </xsl:text>
						<a href="http://code.google.com/p/freemusic/wiki/AboutUs?tm=6" class="ext">Об этом сайте</a>
						<xsl:text> - </xsl:text>
						<a href="http://code.google.com/p/freemusic/issues/list" class="ext">Поддержка</a>
						<xsl:text> - </xsl:text>
						<a href="http://freemusichub.blogspot.com/" class="ext">Наш блог</a>
						<xsl:text> - </xsl:text>
						<a href="/upload">Загрузить альбом</a>
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
				<link rel="stylesheet" type="text/css" href="/static/themes/{@theme}/style.css"/>
				<link rel="shortcut icon" href="/static/favicon.2.ico"/>
			</head>
			<body>
				<div id="closed">
					<xsl:choose>
						<xsl:when test="not(@login-uri) or closed/@saved">
							<h2>Доступа пока нет</h2>
							<p>Вы получите приглашение как только придёт время.</p>
						</xsl:when>
						<xsl:otherwise>
							<h2>Мы ещё не открыты</h2>
							<p>Сайт находится на стадии закрытого тестирования. Вы можете оставить свой почтовый адрес, и мы пригласим вас к этому процессу, как только будем готовы.</p>
							<form method="post" action="/users/invite">
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
		<!--
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
				<xsl:if test="/page/@user">
					<li><a href="/my/collection">Моя коллекция</a></li>
				</xsl:if>
			</ul>
			<ul>
				<li><a href="/artists">Исполнители</a></li>
			</ul>
			<div class="uya">
				<p>Музыкант?</p>
				<a href="/upload">Загрузи свой альбом</a>
			</div>

			<xsl:if test="labels/label">
				<h3><a href="/labels">Метки</a></h3>
				<xsl:apply-templates select="labels" mode="linked">
					<xsl:with-param name="uri">/?label=</xsl:with-param>
				</xsl:apply-templates>
			</xsl:if>
		</div>
		-->
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
				<li>
					<xsl:attribute name="class">
						<xsl:text>album pos</xsl:text>
						<xsl:value-of select="(position() - 1) mod 4"/>
					</xsl:attribute>
					<a href="/album/{@id}" class="cover">
						<img>
							<xsl:attribute name="src">
								<xsl:value-of select="@image"/>
								<xsl:if test="not(@image)">/static/default_album_large.png</xsl:if>
							</xsl:attribute>
						</img>
						<span class="jewelcase"/>
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
					<xsl:apply-templates select="@rate"/>
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
				<a href="{@original}" class="ext">
					<img src="{@medium}" width="200" height="200" alt="medium"/>
				</a>
			</xsl:when>
			<xsl:otherwise>
				<img src="/static/default_album_large.png" width="200" height="200" alt="default image"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="labels" mode="linked">
		<xsl:param name="uri"/>
		<xsl:param name="weight"/>
		<xsl:param name="text"/>
		<div class="labels">
			<xsl:if test="$text">
				<h3><xsl:value-of select="$text"/></h3>
			</xsl:if>
			<ul class="labels">
				<xsl:for-each select="label[text()]">
					<xsl:sort select="text()"/>
					<li>
						<a href="{$uri}{@uri}">
							<xsl:value-of select="text()"/>
						</a>
						<xsl:if test="$weight">
							<sup>
								<xsl:value-of select="@weight"/>
							</sup>
						</xsl:if>
					</li>
				</xsl:for-each>
			</ul>
		</div>
	</xsl:template>

	<!-- Вывод рецензии на альбом. -->
	<xsl:template match="review[@comment]">
		<xsl:param name="title"/>
		<div class="review">
			<div class="meta" id="review:{@author-nickname}">
				<span>
					<xsl:apply-templates select="@pubDate"/>
				</span>
				<span>
					<a href="/u/{@author-nickname}" class="u">
						<xsl:value-of select="@author-nickname"/>
					</a>
					<xsl:text> </xsl:text>
					<xsl:if test="$title">
						<xsl:text> на </xsl:text>
						<span>
							<a href="/album/{@album-id}">
								<xsl:value-of select="@album-name"/>
							</a>
							<xsl:text> от </xsl:text>
							<a href="/artist/{@artist-id}">
								<xsl:value-of select="@artist-name"/>
							</a>
						</span>
					</xsl:if>
				</span>
				<span>
					<xsl:apply-templates select="@average"/>
				</span>
			</div>
			<p>
				<xsl:value-of select="@comment"/>
			</p>
		</div>
	</xsl:template>

	<!-- Вывод звёздочек для альбома -->
	<xsl:template match="album/@rate|review/@average">
		<xsl:choose>
			<xsl:when test=".=5">
				<span class="smallstars rate-5"><span>5/5</span></span>
			</xsl:when>
			<xsl:when test=".=4">
				<span class="smallstars rate-4"><span>4/5</span></span>
			</xsl:when>
			<xsl:when test=".=3">
				<span class="smallstars rate-3"><span>3/5</span></span>
			</xsl:when>
			<xsl:when test=".=2">
				<span class="smallstars rate-2">2/5</span>
			</xsl:when>
			<xsl:when test=".=1">
				<span class="smallstars rate-1">1/5</span>
			</xsl:when>
			<xsl:otherwise>
				<span class="smallstars rate-0">нет оценок</span>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="@pubDate">
		<xsl:value-of select="concat(substring(.,9,2),'.',substring(.,6,2),'.',substring(.,1,4))"/>
	</xsl:template>
</xsl:stylesheet>
