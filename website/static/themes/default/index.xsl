<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="/page/index">
		<div id="index" class="onecol">
			<p class="intro">Этот сайт помогает искать и распространять свободную музыку. <a class="ext" href="http://code.google.com/p/freemusic/wiki/AboutUs?tm=6">Подробнее</a></p>
			<xsl:call-template name="lnav"/>
			<div class="right">
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
			</div>
		</div>
	</xsl:template>
</xsl:stylesheet>
