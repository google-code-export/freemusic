<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="player">
		<h2>Проигрыватель</h2>
		<table class="basic">
			<thead>
				<tr>
					<th>Композиция</th>
					<th>Альбом</th>
					<th>Исполнитель</th>
					<th>Время</th>
				</tr>
			</thead>
			<tbody>
				<xsl:for-each select="track">
					<tr>
						<td>
							<a href="/track/{@id}">
								<xsl:value-of select="@title"/>
							</a>
						</td>
						<td>
							<a href="/album/{@album-id}">
								<xsl:value-of select="@album-name"/>
							</a>
						</td>
						<td>
							<a href="/artist/{@artist-id}">
								<xsl:value-of select="@artist-name"/>
							</a>
						</td>
						<td>
							<xsl:value-of select="@duration"/>
						</td>
					</tr>
				</xsl:for-each>
			</tbody>
		</table>
	</xsl:template>
</xsl:stylesheet>
