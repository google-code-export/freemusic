<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="/page/events">
		<div id="events" class="onecol">
			<h2>Расписание концертов</h2>
			<xsl:choose>
				<xsl:when test="event">
					<table>
						<thead>
							<tr>
							<th>Когда</th>
							<th>Кто</th>
							<th>Где</th>
							</tr>
						</thead>
						<tbody>
							<xsl:for-each select="event">
								<xsl:sort select="@date"/>
								<tr>
									<td>
										<xsl:value-of select="concat(substring(@date,9,2),'.',substring(@date,6,2),'.',substring(@date,3,2))"/>
									</td>
									<td class="artist">
										<a href="/artist/{@artist-id}">
											<xsl:value-of select="@artist-name"/>
										</a>
									</td>
									<td>
										<a href="{@url}" target="_blank">
											<xsl:value-of select="concat(@title,' @ ',@venue,' (',@city,')')"/>
										</a>
									</td>
								</tr>
							</xsl:for-each>
						</tbody>
					</table>
				</xsl:when>
				<xsl:otherwise>
					<p>Нет информации о предстоящих концертах музыкантов, представленных на нашем сайте.</p>
				</xsl:otherwise>
			</xsl:choose>
			<p>Для создания этой афиши используются данные сайта <a href="http://www.lastfm.ru/">Last.fm</a>. Чтобы попасть в неё, <a href="http://www.lastfm.ru/events/add">добавьте событие</a>.</p>
		</div>
	</xsl:template>
</xsl:stylesheet>
