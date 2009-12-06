<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output
		omit-xml-declaration="yes"
		method="xml"
		version="1.0"
		encoding="utf-8"
		indent="no"
		doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"
		doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
		/>
	<xsl:template match="/page">
		<html lang="{@lang}">
			<body>
				<xsl:apply-templates select="*"/>
			</body>
		</html>
	</xsl:template>

	<xsl:template match="/page/album">
		<h1>
			<xsl:value-of select="@name"/>
		</h1>
		<xsl:if test="@pubDate">
			<p>Published on <xsl:value-of select="@pubDate"/></p>
		</xsl:if>
		<xsl:apply-templates select="cover"/>
		<xsl:apply-templates select="tracks"/>
		<xsl:apply-templates select="files"/>
	</xsl:template>

	<xsl:template match="cover">
		<img src="{@uri}" alt="cover"/>
	</xsl:template>

	<xsl:template match="tracks">
		<h2>Tracks</h2>
		<ul>
			<xsl:apply-templates select="track"/>
		</ul>
	</xsl:template>

	<xsl:template match="track">
		<li>
			<a href="{@mp3}">
				<xsl:value-of select="@title"/>
			</a>
		</li>
	</xsl:template>

	<xsl:template match="files">
		<h2><a href="{file/@uri}">Download</a></h2>
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

	<xsl:template match="upload-xml-form">
		<h1>Upload XML</h1>
		<form method="post" enctype="multipart/form-data">
			<div>
				<input type="file" name="xml"/>
			</div>
			<input type="submit"/>
		</form>
	</xsl:template>
</xsl:stylesheet>
