<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xhtml="http://www.w3.org/1999/xhtml">
	<xsl:output method="xml"
				version="1.0"
				encoding="UTF-8"
				doctype-public="-//W3C//DTD XHTML 1.1//EN"
				doctype-system="http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"
				indent="yes"/>

	<xsl:template match="xhtml:html">
		<html>
			<head>
				<title><xsl:value-of select=".//xhtml:title/text()"/></title>
				<link rel="stylesheet" type="text/css" href="/fmh-static/style.css"/>
			</head>
			<body>
				<xsl:apply-templates select="xhtml:body"/>
			</body>
		</html>
	</xsl:template>

	<!-- Страница альбома -->
	<xsl:template match="xhtml:body[@class='album-view']">
		<h1><xsl:value-of select="xhtml:h1/text()"/></h1>
		<p title="Автор"><xsl:value-of select="xhtml:p[@class='artist']/xhtml:span/text()"/></p>
		<ul class="links">
			<li>
				<a href="{xhtml:p[@class='download_link']/xhtml:a/text()}">Скачать альбом</a>
			</li>
			<li>
				<a href="{xhtml:p[@class='homepage']/xhtml:a/text()}">Сайт исполнителя</a>
			</li>
		</ul>
	</xsl:template>

	<!-- Форма добавления альбома -->
	<xsl:template match="xhtml:body[@class='add-album']">
		<h1>Добавление альбома</h1>
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
