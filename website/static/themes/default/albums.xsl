<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<!-- Просмотр альбома -->
	<xsl:template match="/page/album">
		<div id="album" class="twocol">
			<xsl:apply-templates select="." mode="h2"/>
			<div class="left">
				<xsl:apply-templates select="images/image[@type='front']" mode="medium"/>
				<xsl:if test="count(images/image) &gt; 1">
					<ul class="moreimg">
						<xsl:for-each select="images/image">
							<li>
								<a href="{@original}" target="_blank">
									<img src="{@medium}" width="50" height="50" alt="{@name}"/>
								</a>
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<xsl:apply-templates select="labels" mode="linked">
					<xsl:with-param name="uri">/?label=</xsl:with-param>
				</xsl:apply-templates>
				<ul>
					<li>
						<a href="{files/file/@uri}">Скачать альбом</a>
					</li>
					<xsl:if test="/page/@email = @owner or /page/@is-admin">
						<li>
							<a href="/album/{@id}/edit">Отредактировать</a>
						</li>
						<li>
							<a href="/album/{@id}/delete">Удалить</a>
						</li>
					</xsl:if>
				</ul>
			</div>
			<div class="right">
				<table class="tracklist">
					<tbody>
						<xsl:for-each select="tracks/track">
							<tr>
								<td class="r">
									<xsl:value-of select="position()"/>
									<xsl:text>.</xsl:text>
								</td>
								<td class="u"></td>
								<td class="track">
									<a href="/track/{@id}">
										<xsl:value-of select="@title"/>
									</a>
								</td>
								<td class="dur">
									<xsl:value-of select="@duration"/>
								</td>
								<td class="dl">
									<a href="{@ogg-link}">ogg</a>
									<xsl:text>&#160;</xsl:text>
									<a href="{@mp3-link}">mp3</a>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<xsl:if test="@pubDate">
					<p>Выпущен <xsl:value-of select="concat(substring(@pubDate,9,2),'.',substring(@pubDate,6,2),'.',substring(@pubDate,1,4))"/></p>
				</xsl:if>
			</div>
		</div>
	</xsl:template>

	<!-- Форма редактирования альбома -->
	<xsl:template match="/page/form/album">
		<div class="twocol">
			<div class="right">
				<xsl:apply-templates select="." mode="h2"/>
				<form method="post" class="gen eal">
					<div>
						<label>
							<span>Заголовок:</span>
							<input type="text" class="text" name="name" value="{@name}"/>
						</label>
					</div>
					<div>
						<label>
							<span>Дата публикации:</span>
							<input type="text" class="text" name="pubDate" value="{@pubDate}"/>
						</label>
					</div>
					<div>
						<label>
							<span>Описание:</span>
							<textarea class="text" name="text">
								<xsl:value-of select="@text"/>
							</textarea>
						</label>
					</div>
					<div>
						<label>
							<span>Метки:</span>
							<input type="text" class="text" name="labels">
								<xsl:attribute name="value">
									<xsl:for-each select="labels/label">
										<xsl:value-of select="text()"/>
										<xsl:if test="position()!=last()">
											<xsl:text>, </xsl:text>
										</xsl:if>
									</xsl:for-each>
								</xsl:attribute>
							</input>
						</label>
					</div>
					<fieldset>
						<legend>Названия дорожек:</legend>
						<ol>
							<xsl:for-each select="tracks/track">
								<xsl:sort select="@number" data-type="number"/>
								<li>
									<input type="text" class="text" name="track.{@id}" value="{@title}"/>&#160;<a href="/track/{@id}" target="_blank">#</a>
								</li>
							</xsl:for-each>
						</ol>
					</fieldset>
					<div>
						<input type="submit" value="Сохранить изменения"/> или <a href="/album/{@id}">вернуться без сохранения</a>
					</div>
				</form>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="album" mode="h2">
		<h2>
			<xsl:text>«</xsl:text>
			<xsl:value-of select="@name"/>
			<xsl:text>»</xsl:text>
			<small>
				<xsl:text> от </xsl:text>
				<a href="/artist/{@artist-id}">
					<xsl:value-of select="@artist-name"/>
				</a>
			</small>
		</h2>
	</xsl:template>

	<xsl:template match="delete-album">
		<div class="onecol">
			<h2>Удаление альбома</h2>
			<form method="post">
				<p>Действительно ли ты хочешь удалить альбом <a href="/album/{@id}"><xsl:value-of select="@name"/></a> исполнителя <a href="/artist/{@artist-id}"><xsl:value-of select="@artist-name"/></a>?</p>
				<input type="submit" name="confirm" value="Да"/> &#160; <a href="/album/{@id}">Нет</a>
			</form>
		</div>
	</xsl:template>
</xsl:stylesheet>