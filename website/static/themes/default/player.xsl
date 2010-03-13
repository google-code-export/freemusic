<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="player">
		<div id="player">
			<h2>Проигрыватель</h2>
			<xsl:apply-templates select="artists"/>
			<xsl:apply-templates select="." mode="tracks"/>
		</div>
	</xsl:template>

	<xsl:template match="artists">
		<div class="filter">
			<ul class="artists">
				<xsl:for-each select="artist">
					<xsl:sort select="@sort"/>
					<li>
						<label>
							<input type="checkbox" name="artist" value="{@id}" checked="checked"/>
							<xsl:value-of select="@name"/>
						</label>
					</li>
				</xsl:for-each>
			</ul>
			<ul class="albums">
				<xsl:for-each select="artist/album">
					<xsl:sort select="@name"/>
					<li class="artist-{../@id}">
						<label>
							<input type="checkbox" name="album" value="{@id}" checked="checked"/>
							<xsl:value-of select="@name"/>
						</label>
					</li>
				</xsl:for-each>
			</ul>
		</div>
	</xsl:template>

	<xsl:template match="player" mode="tracks">
		<table class="ptl basic tracklist">
			<thead>
				<tr>
					<th/>
					<th>Композиция</th>
					<th>Альбом</th>
					<th>Исполнитель</th>
					<th>Время</th>
				</tr>
			</thead>
			<tbody>
				<xsl:for-each select="artists/artist/album/track">
					<tr id="track-{@id}" class="track artist-{@artist-id} album-{@album-id}">
						<td class="controls">
							<span/>
						</td>
						<td>
							<a href="/track/{@id}">
								<xsl:value-of select="@title"/>
							</a>
							<a class="ogg" href="{@ogg-link}">ogg</a>
							<a class="mp3" href="{@mp3-link}">mp3</a>
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
						<td class="pb">
							<xsl:value-of select="@duration"/>
						</td>
					</tr>
				</xsl:for-each>
			</tbody>
		</table>
	</xsl:template>
</xsl:stylesheet>
