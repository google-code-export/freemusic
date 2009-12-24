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
					<div id="footer">© ebm.net.ru - <a href="/">Главная</a> - <a href="http://code.google.com/p/freemusic/">О проекте</a> - <a href="/_ah/admin">Админка</a> - <a href="/upload/xml">Загрузить XML</a></div>
				</div>
			</body>
		</html>
	</xsl:template>

	<!--
	<xsl:template match="/page/album">
		<div id="album">
			<div class="images">
				<xsl:apply-templates select="images/image[@type='medium']"/>
			</div>
			<h2>
				<xsl:value-of select="@name"/>
				<small> by <a href="/music/{@artist}/"><xsl:value-of select="@artist"/></a></small>
			</h2>
			<xsl:if test="@pubDate">
				<p>Published on <xsl:value-of select="@pubDate"/></p>
			</xsl:if>
			<xsl:apply-templates select="cover"/>
			<xsl:apply-templates select="tracks"/>
			<xsl:apply-templates select="files"/>
		</div>
	</xsl:template>
	-->

	<xsl:template match="/page/album">
		<div id="album">
			<h2>
				<xsl:value-of select="@name"/>
				<small> by <a href="/music/{@artist}/"><xsl:value-of select="@artist"/></a></small>
			</h2>
			<div class="left">
				<xsl:apply-templates select="images/image[@type='medium']"/>
				<p class="dl"><a href="{files/file/@uri}">Скачать альбом</a> ▼</p>
			</div>
			<div class="right">
				<table>
					<tbody>
						<xsl:for-each select="tracks/track">
							<tr>
								<td>
									<xsl:value-of select="position()"/>
									<xsl:text>.</xsl:text>
								</td>
								<td>
									<a href="{@mp3}">
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

	<xsl:template match="/page/index">
		<div id="index" class="twocol">
			<div class="left">
				<ul>
					<li><a href="/">Свежие</a></li>
					<li><a href="/">Популярные</a></li>
					<li><a href="/">Рекомендуемые</a></li>
				</ul>
				<div class="uya">
					<p>Музыкант?</p>
					<a href="/upload">Загрузи свой альбом</a>
				</div>
			</div>
			<div class="right">
				<ul class="tiles">
					<xsl:for-each select="album">
						<li class="album">
							<a href="album/{@id}">
								<xsl:apply-templates select="images/image[@type=$index-image-type]"/>
							</a>
							<div>
								<a class="n" href="album/{@id}">
									<xsl:value-of select="@name"/>
								</a>
								<small>
									<xsl:text> by </xsl:text>
									<xsl:value-of select="@artist"/>
								</small>
							</div>
						</li>
					</xsl:for-each>
				</ul>
				<ul class="pager">
					<xsl:if test="@skip &gt; 14">
						<li>
							<a href="?skip={@skip - 15}">« Назад</a>
						</li>
					</xsl:if>
					<xsl:if test="count(album) = 15">
						<!-- TODO: аяксовая подгрузка ещё 15 альбомов сюда же -->
						<li>
							<a href="?skip={@skip + 15}">Ещё »</a>
						</li>
					</xsl:if>
				</ul>
			</div><!-- right column -->
		</div>
	</xsl:template>

	<xsl:template match="image">
		<img src="{@uri}" alt="image" width="{@width}" height="{@height}"/>
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
			<div>
				<input type="submit" value="Save" class="button"/>
			</div>
		</form>
	</xsl:template>

	<xsl:template match="s3-upload-form">
		<h1>Загрузка нового альбома</h1>
		<!--
		http://docs.amazonwebservices.com/AmazonS3/2006-03-01/index.html?UsingHTTPPOST.html
		-->
		<form action="http://{@bucket}.s3-external-3.amazonaws.com/" method="post" enctype="multipart/form-data">
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
				<input type="submit" value="Загрузить файл"/> или <a href="/">отменить загрузку</a>
			</div>
		</form>
	</xsl:template>
</xsl:stylesheet>
