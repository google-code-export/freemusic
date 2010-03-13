<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="user">
		<h2>Профиль пользователя <xsl:value-of select="@nickname"/></h2>
		<div id="profile" class="blocks">
			<div id="user-profile">
				<img src="http://www.gravatar.com/avatar.php?gravatar_id={@hash}&amp;size=80" width="80" height="80"/>
				<ul>
					<!--
					<li><a href="/reviews?author={@nickname}">Рецензии</a></li>
					<li><a href="/player?user={@nickname}">Коллекция</a></li>
					-->
					<li>На сайте с <xsl:apply-templates select="@pubDate"/></li>
				</ul>
			</div>
			<xsl:apply-templates select="stars"/>
			<xsl:apply-templates select="reviews"/>
		</div>
	</xsl:template>

		<xsl:template match="user/stars">
			<div id="user-stars" class="album-stars block list">
				<h3>Коллекция <small><a href="http://code.google.com/p/freemusic/wiki/Collection" class="ext">что это такое?</a></small></h3>
				<table>
					<tbody>
						<xsl:for-each select="star">
							<xsl:sort select="@pubDate" order="descending"/>
							<tr>
								<td>
									<span class="star on">
										<a href="{@album-id}"/>
									</span>
								</td>
								<td>
									<a href="/album/{@album-id}">
										<xsl:value-of select="@album-name"/>
									</a>
									<span class="artist">
										<xsl:text> от </xsl:text>
										<a href="/artist/{@artist-id}">
											<xsl:value-of select="@artist-name"/>
										</a>
									</span>
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

		<xsl:template match="user/reviews">
			<div id="user-reviews" class="block list">
				<h3><a href="/reviews" title="Открыть все рецензии">Рецензии</a></h3>
				<table>
					<tbody>
						<xsl:for-each select="review">
							<xsl:sort select="@pubDate" order="descending"/>
							<tr>
								<td>
									<xsl:apply-templates select="@average"/>
								</td>
								<td>
									<a href="/album/{@album-id}#review:{/page/@user}">
										<xsl:value-of select="@album-name"/>
									</a>
									<span class="artist">
										<xsl:text> от </xsl:text>
										<a href="/artist/{@artist-id}">
											<xsl:value-of select="@artist-name"/>
										</a>
									</span>
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
</xsl:stylesheet>
