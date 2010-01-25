<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<!-- Вывод информации об исполнителе -->
	<xsl:template match="/page/artist">
		<div class="onecol">
			<div class="right">
				<h2>
					<xsl:value-of select="@name"/>
				</h2>
				<xsl:apply-templates select="albums" mode="tiles"/>
				<xsl:if test="not(albums)">
					<p>Об этом исполнителе пока ничего не известно.</p>
				</xsl:if>
			</div>
		</div>
	</xsl:template>

	<!-- Вывод списка исполнителей -->
	<xsl:template match="artists">
		<div class="twocol">
			<xsl:call-template name="lnav"/>
			<div class="right">
				<h2>Все исполнители</h2>
				<ul class="artists">
					<xsl:for-each select="artist">
						<xsl:sort select="@name"/>
						<li>
							<a href="artist/{@id}">
								<xsl:value-of select="@name"/>
							</a>
						</li>
					</xsl:for-each>
				</ul>
			</div>
		</div>
	</xsl:template>
</xsl:stylesheet>
