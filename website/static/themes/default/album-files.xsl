<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="/page/album">
		<div id="album" class="twocolrev">
			<h2>
				<xsl:text>Файлы для «</xsl:text>
				<a href="/album/{@id}">
					<xsl:value-of select="@name"/>
				</a>
				<xsl:text>»</xsl:text>
			</h2>
			<table>
				<tbody>
					<xsl:for-each select="files/file">
						<tr>
							<td>
								<a href="{@uri}">
									<xsl:value-of select="@name"/>
								</a>
							</td>
							<td>
								<xsl:if test="contains(@name,'.zip')">
									<a href="{@uri}?torrent">torrent</a>
								</xsl:if>
							</td>
						</tr>
					</xsl:for-each>
				</tbody>
			</table>
		</div>
	</xsl:template>
</xsl:stylesheet>
