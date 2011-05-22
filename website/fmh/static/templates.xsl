<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xhtml="http://www.w3.org/1999/xhtml">
	<xsl:output method="xml"
				version="1.0"
				encoding="UTF-8"
				doctype-public="-//W3C//DTD XHTML 1.1//EN"
				doctype-system="http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"
				indent="yes"/>

	<xsl:template match="xhtml:html">
		<xsl:variable name="title">
			<xsl:value-of select="xhtml:head/xhtml:title/text()"/>
		</xsl:variable>
		<html>
			<head>
				<title><xsl:value-of select="$title"/> — Free Music Hub</title>
				<link rel="stylesheet" type="text/css" href="/fmh-static/style.css"/>
				<link rel="icon" type="image/x-icon" href="/fmh-static/favicon.ico"/>
			</head>
			<body>
				<div id="wrapper">
					<xsl:apply-templates select="xhtml:body">
						<xsl:with-param name="title" select="$title"/>
					</xsl:apply-templates>
				</div>
			</body>
		</html>
	</xsl:template>

	<!-- Страница альбома -->
	<xsl:template match="xhtml:body[@class='album-view']">
		<xsl:param name="title"/>
		<xsl:variable name="album_id" select="xhtml:dl/xhtml:dd[@id='album_id']/text()"/>
		<xsl:variable name="album_title" select="xhtml:dl/xhtml:dd[@id='album_title']/text()"/>
		<xsl:variable name="album_artist" select="xhtml:dl/xhtml:dd[@id='album_artist']/text()"/>
		<xsl:variable name="homepage" select="xhtml:dl/xhtml:dd[@id='homepage']/text()"/>
		<xsl:variable name="cover" select="xhtml:dl/xhtml:dd[@id='cover']/text()"/>
		<div id="album-view">
            <img class="cover" src="{$cover}" alt="Обложка"/>
			<div class="info">
				<h1><xsl:value-of select="$album_title"/></h1>
				<p class="artist">
					<a class="external" href="{$homepage}">
						<xsl:value-of select="$album_artist"/>
					</a>
					<xsl:text> (1980)</xsl:text>
				</p>
				<xsl:if test="xhtml:p[@class='positive_reviews']">
					<p class="positive_reviews">Положительных отзывов: <xsl:value-of select="xhtml:p[@class='positive_reviews']/xhtml:span/text()"/></p>
				</xsl:if>
				<p class="download">
					<a href="/album/{$album_id}/download">Скачать альбом</a>
				</p>
			</div>

			<xsl:apply-templates select="xhtml:ul[@id='reviews']"/>

            <div id="review">
                <h2>Напишите рецензию</h2>
                <form method="post" action="/album/{$album_id}/review">
                    <div class="control check">
                        <label>
                            <input type="checkbox" name="likes" value="1" checked="checked"/>
                            <span>нравится</span>
                        </label>
                    </div>
                    <div class="control">
						<label>Комментарий:</label>
                        <textarea name="comment"></textarea>
                    </div>
					<div class="control">
						<label>Ваш email:</label>
						<input type="text" name="email"/>
					</div>
					<button>Отправить</button>
                </form>
            </div>
		</div>
	</xsl:template>

		<xsl:template match="xhtml:ul[@id='reviews']">
			<div id="reviews">
				<h2>Отзывы</h2>
				<ul>
					<xsl:for-each select="xhtml:li">
						<li>
							<img class="avatar" src="{@avatar}?s=50"/>
							<p class="comment"><xsl:value-of select="text()"/></p>
							<p class="meta">
								<xsl:value-of select="@date"/>
								<xsl:if test="@likes">
									<xsl:text> </xsl:text>
									<span>нравится</span>
								</xsl:if>
							</p>
						</li>
					</xsl:for-each>
				</ul>
			</div>
		</xsl:template>

	<!-- Форма добавления альбома -->
	<xsl:template match="xhtml:body[@class='add-album']">
		<xsl:apply-templates select="xhtml:form"/>
	</xsl:template>

	<!-- Вывод произвольной формы -->
	<xsl:template match="xhtml:form">
		<form method="{@method}" action="{@action}">
			<xsl:apply-templates select="*"/>
		</form>
	</xsl:template>

		<xsl:template match="xhtml:input">
			<div class="control">
				<xsl:if test="@placeholder">
					<label><xsl:value-of select="@placeholder"/>:</label>
				</xsl:if>
				<input type="{@type}" name="{@name}" value="{@value}" class="text"/>
			</div>
		</xsl:template>

		<xsl:template match="xhtml:button">
			<button>
				<xsl:value-of select="text()"/>
			</button>
		</xsl:template>
</xsl:stylesheet>
