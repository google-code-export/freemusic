<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<!-- Вывод информации об исполнителе -->
	<xsl:template match="/page/artist">
		<div id="artist" class="onecol">
			<div class="right blocks">
				<h2>
					<xsl:value-of select="@name"/>
					<small><a href="http://www.lastfm.ru/music/{@name}" class="ext">Last.fm</a></small>
				</h2>
				<xsl:apply-templates select="albums"/>
				<xsl:apply-templates select="reviews"/>
				<xsl:apply-templates select="events"/>
			</div>
		</div>
	</xsl:template>

		<xsl:template match="albums">
			<div id="artist-albums" class="list">
				<h3>Альбомы</h3>
				<xsl:apply-templates select="album" mode="tile"/>
			</div>
		</xsl:template>

		<xsl:template match="reviews">
			<div id="artist-reviews" class="block list">
				<h3><a href="/reviews">Рецензии</a></h3>
				<table>
					<tbody>
						<xsl:for-each select="review">
							<xsl:sort select="@pubDate" order="descending"/>
							<tr>
								<td>
									<xsl:apply-templates select="@average"/>
								</td>
								<td>
									<a href="/u/{@author}" class="username">
										<xsl:value-of select="@author"/>
									</a>
								</td>
								<td>
									<a href="/album/{@album-id}">
										<xsl:value-of select="@album-name"/>
									</a>
								</td>
								<td>
									<xsl:apply-templates select="@pubDate"/>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</div>
		</xsl:template>

		<xsl:template match="events">
			<div id="artist-events" class="block list">
				<h3><a href="/events">Концерты</a> <small><a href="http://www.lastfm.ru/events/add?artistNames[]={../@name}" class="ext">добавить</a></small></h3>
				<table>
					<tbody>
						<xsl:for-each select="event">
							<tr>
								<td>
									<xsl:apply-templates select="@date"/>
								</td>
								<td>
									<a href="{@url}" class="ext">
										<xsl:value-of select="@city"/>
									</a>
									<xsl:value-of select="concat(' (',@venue,')')"/>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
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
						<xsl:sort select="@sortname"/>
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
