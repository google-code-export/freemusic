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
			</head>
			<body>
				<xsl:apply-templates select="xhtml:body"/>
			</body>
		</html>
	</xsl:template>

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
</xsl:stylesheet>
