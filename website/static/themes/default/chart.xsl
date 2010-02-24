<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="chart">
		<div id="chart">
			<h2>Рейтинг исполнителей <small><a href="http://code.google.com/p/freemusic/wiki/Charts" class="ext help">как это работает?</a></small></h2>

			<ol>
				<xsl:for-each select="artist">
					<xsl:sort select="@listeners" order="descending" data-type="number"/>
					<li>
						<a href="/artist/{@id}">
							<xsl:value-of select="@name"/>
						</a>
						<xsl:text> </xsl:text>
						<small>
							<a href="{@lastfm-url}" class="ext">
								<xsl:value-of select="@listeners"/>
							</a>
						</small>
					</li>
				</xsl:for-each>
			</ol>
		</div>
	</xsl:template>
</xsl:stylesheet>
