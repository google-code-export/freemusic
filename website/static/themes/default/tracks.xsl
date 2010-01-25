<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<!-- Вывод отдельной дорожки -->
	<xsl:template match="/page/track">
		<div class="twocol">
			<div class="right">
				<h2>
					<xsl:value-of select="@title"/>
				</h2>
				<p><xsl:if test="@number">Дорожка №<xsl:value-of select="@number"/> из</xsl:if><xsl:if test="not(@number)">Из</xsl:if> альбома <a href="/album/{@album-id}"><xsl:value-of select="@album-name"/></a>.</p>
				<xsl:if test="@mp3-link or @ogg-link">
					<audio controls="controls">
						<xsl:if test="@mp3-link">
							<source src="{@mp3-link}" type="audio/mp3"/>
						</xsl:if>
						<xsl:if test="@ogg-link">
							<source src="{@ogg-link}" type="audio/ogg; codecs=vorbis"/>
						</xsl:if>
					</audio>
				</xsl:if>
				<ul>
					<xsl:if test="@mp3-link">
						<li>
							<a href="{@mp3-link}">Скачать MP3</a>
						</li>
					</xsl:if>
					<xsl:if test="@ogg-link">
						<li>
							<a href="{@ogg-link}">Скачать OGG/Vorbis</a>
						</li>
					</xsl:if>
				</ul>
			</div>
		</div>
	</xsl:template>
</xsl:stylesheet>
