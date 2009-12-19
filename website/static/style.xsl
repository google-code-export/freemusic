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

	<xsl:variable name="index-image-type">medium</xsl:variable><!-- thumbnail, medium -->

	<xsl:template match="/page">
		<html lang="{@lang}">
			<head>
				<title>music 3.5</title>
				<link rel="stylesheet" type="text/css" href="/static/style.css"/>
				<link rel="shortcut icon" href="/static/favicon.2.ico"/>
			</head>
			<body>
				<xsl:apply-templates select="*"/>
				<div id="footer">
					<hr/>
					<p>
						<a href="/">home</a>
						<a href="http://code.google.com/p/freemusic/">Google Code</a>
						<a href="/_ah/admin">admin console</a>
						<a href="/upload/xml">upload xml</a>
					</p>
				</div>
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

	<xsl:template match="/page/index">
		<h1>New albums</h1>
		<ul id="index">
			<xsl:for-each select="album">
				<li>
					<a href="music/{@artist}/{@name}/">
						<xsl:apply-templates select="images/image[@type=$index-image-type]"/>
					</a>
					<div>
						<a class="n" href="music/{@artist}/{@name}/">
							<xsl:value-of select="@name"/>
						</a>
						<span>
							<xsl:text> by </xsl:text>
						</span>
						<a class="a" href="music/{@artist}/">
							<xsl:value-of select="@artist"/>
						</a>
					</div>
				</li>
			</xsl:for-each>
		</ul>
	</xsl:template>

	<xsl:template match="image">
		<img src="{@uri}" alt="image" width="{@width}" height="{@height}"/>
	</xsl:template>
</xsl:stylesheet>
