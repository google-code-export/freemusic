<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="/page/index">
		<div id="index" class="onecol">
			<xsl:call-template name="lnav"/>
			<div class="right">
				<xsl:apply-templates select="albums" mode="tiles"/>
				<ul class="pager">
					<xsl:if test="@skip &gt; 15">
						<li>
							<a href="?skip={@skip - 16}">« Назад</a>
						</li>
					</xsl:if>
					<xsl:if test="count(albums/album) = 16">
						<!-- TODO: аяксовая подгрузка ещё 16 альбомов сюда же -->
						<li>
							<a href="?skip={@skip + 16}">Ещё »</a>
						</li>
					</xsl:if>
				</ul>
			</div>
		</div>
	</xsl:template>
</xsl:stylesheet>
