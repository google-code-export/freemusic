<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="reviews">
		<h2>
			<xsl:choose>
				<xsl:when test="@author">Рецензии пользователя <a href="/u/{@author}"><xsl:value-of select="@author"/></a></xsl:when>
				<xsl:otherwise>Последние рецензии</xsl:otherwise>
			</xsl:choose>
			<xsl:text> </xsl:text>
			<small><a class="help ext" href="http://code.google.com/p/freemusic/wiki/Reviews">что это?</a></small>
		</h2>
		<xsl:apply-templates select="review">
			<xsl:sort select="@pubDate" order="descending"/>
			<xsl:with-param name="author" select="@author"/>
			<xsl:with-param name="title">yes</xsl:with-param>
		</xsl:apply-templates>
	</xsl:template>

	<xsl:template match="review">
		<xsl:param name="author"/>
		<div class="review">
			<div class="meta">
				<xsl:apply-templates select="@average"/>
				<xsl:if test="not($author)">
					<a href="/u/{@author-nickname}" class="u">
						<xsl:value-of select="@author-nickname"/>
					</a>
					<xsl:text>: &#160; </xsl:text>
				</xsl:if>
				<xsl:text>«</xsl:text>
				<a href="/album/{@album-id}">
					<xsl:value-of select="@album-name"/>
				</a>
				<xsl:text>» от </xsl:text>
				<a href="/artist/{@artist-id}">
					<xsl:value-of select="@artist-name"/>
				</a>
				<xsl:text> (</xsl:text>
				<xsl:apply-templates select="@pubDate"/>
				<xsl:text>)</xsl:text>
			</div>
			<p>
				<xsl:value-of select="@comment"/>
			</p>
		</div>
	</xsl:template>
</xsl:stylesheet>
