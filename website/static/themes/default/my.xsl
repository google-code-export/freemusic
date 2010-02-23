<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="/page/my">
		<div id="my" class="onecol">
			<h2>Твоя коллекция <small><a href="http://code.google.com/p/freemusic/wiki/Collection" class="help" target="_blank">что это?</a></small></h2>
			<xsl:choose>
				<xsl:when test="albums/album">
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
				</xsl:when>
				<xsl:otherwise>
					<p>Коллекция пока пуста. Сюда можно добавить альбом, нажав на специальную звёздочку:</p>
					<img src="http://freemusic.googlecode.com/files/album-star-screenshot.png" alt="screenshot" width="400" height="240"/>
				</xsl:otherwise>
			</xsl:choose>
			<xsl:apply-templates select="reviews" mode="my"/>
		</div>
	</xsl:template>

		<xsl:template match="reviews[review]" mode="my">
			<h2>Рецензии</h2>
			<xsl:for-each select="review">
				<xsl:sort select="@pubDate" order="descending"/>
				<div>
					<p class="meta">
						<xsl:apply-templates select="@pubDate"/>
						<xsl:text>, на «</xsl:text>
						<a href="/album/{@album-id}">
							<xsl:value-of select="@album-name"/>
						</a>
						<xsl:text>» от </xsl:text>
						<a href="/artist/{@artist-id}">
							<xsl:value-of select="@artist-name"/>
						</a>
						<xsl:text> &#160; </xsl:text>
						<xsl:apply-templates select="@average"/>
					</p>
					<xsl:apply-templates select="@comment" mode="my"/>
				</div>
			</xsl:for-each>
		</xsl:template>

			<xsl:template match="@comment" mode="my">
				<blockquote>
					<xsl:value-of select="."/>
				</blockquote>
			</xsl:template>
</xsl:stylesheet>