<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<!-- Просмотр альбома -->
	<xsl:template match="/page/album">
		<div id="album" class="twocolrev">
			<xsl:apply-templates select="." mode="h2"/>
			<div class="left">
				<xsl:apply-templates select="images/image[@type='front']" mode="album-cover"/>
				<xsl:apply-templates select="labels" mode="linked">
					<xsl:with-param name="uri">/?label=</xsl:with-param>
				</xsl:apply-templates>
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
				<div class="reviews">
					<h3>Мнения пользователей</h3>
					<xsl:if test="not(../review[@author-email = /page/@email])">
						<form action="/album/review" method="post">
							<input type="hidden" name="id" value="{@id}"/>
							<textarea name="comment" class="hidden">Здесь можно написать рецензию.</textarea>
							<xsl:call-template name="review-stars"/>
						</form>
					</xsl:if>
					<xsl:apply-templates select="/page/review" mode="inside"/>
				</div>
			</div>
		</div>
	</xsl:template>

		<!-- Вывод обложки альбома. Если есть больше одной картинки,
		     выводятся скрытые уменьшеныне копии и специальная ссылка
			 для их вывода. -->
		<xsl:template match="image" mode="album-cover">
			<div class="albumcover">
				<a class="main" href="{@original}" target="_blank">
					<img src="{@medium}" alt="image" width="200" height="200"/>
				</a>
				<xsl:if test="count(../image) &gt; 1">
					<p class="moreimg fakelink">Показать другие картинки</p>
					<ul class="moreimg hidden">
						<xsl:for-each select="../image">
							<li>
								<a href="{@original}" target="_blank">
									<img src="{@medium}" width="50" height="50" alt="{@name}"/>
								</a>
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
			</div>
		</xsl:template>

		<xsl:template name="review-stars">
			<table class="stars hidden">
				<tbody>
					<tr>
						<th>Звук:</th>
						<td>
							<input type="hidden" name="sound"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
						</td>
					</tr>
					<tr>
						<th>Вокал:</th>
						<td>
							<input type="hidden" name="vocals"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
						</td>
					</tr>
					<tr>
						<th>Аранжировка:</th>
						<td>
							<input type="hidden" name="arrangement"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
						</td>
					</tr>
					<tr>
						<th>Текст:</th>
						<td>
							<input type="hidden" name="lyrics"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
						</td>
					</tr>
					<tr>
						<th>Профессионализм:</th>
						<td>
							<input type="hidden" name="prof"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
							<span class="star"/>
						</td>
					</tr>
				</tbody>
				<tfoot>
					<tr>
						<td colspan="2">
							<p class="hint">Будьте внимательны, рецензию нельзя будет исправить.</p>
							<input type="submit" value="Отправить"/>
						</td>
					</tr>
				</tfoot>
			</table>
		</xsl:template>

		<xsl:template match="review[@comment]" mode="inside">
			<div class="review">
				<div class="meta">
					<a href="/user/{@author-email}">
						<xsl:value-of select="@author-nickname"/>
					</a>
					<xsl:text> </xsl:text>
					<span>
						<xsl:value-of select="concat(substring(@pubDate,9,2),'.',substring(@pubDate,6,2),'.',substring(@pubDate,1,4))"/>
					</span>
					<span>
						<xsl:apply-templates select="@average"/>
					</span>
				</div>
				<p>
					<xsl:value-of select="@comment"/>
				</p>
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
		<div class="alh">
			<a class="button" href="{files/file/@uri}">Скачать альбом</a>
			<h2>
				<span title="Добавить в коллекцию">
					<xsl:attribute name="class">
						<xsl:text>star</xsl:text>
						<xsl:if test="/page/@star"> on</xsl:if>
					</xsl:attribute>
				</span>
				<xsl:value-of select="@name"/>
				<small>
					<xsl:text> от </xsl:text>
					<a href="/artist/{@artist-id}">
						<xsl:value-of select="@artist-name"/>
					</a>
				</small>
			</h2>
			<div class="alh2">
				<xsl:apply-templates select="@rate"/>
				<xsl:if test="@pubDate">
					<span>Выпущен <xsl:value-of select="concat(substring(@pubDate,9,2),'.',substring(@pubDate,6,2),'.',substring(@pubDate,1,4))"/></span>
				</xsl:if>
				<xsl:if test="/page/@email = @owner or /page/@is-admin">
					<span>
						<a href="/album/{@id}/edit">Отредактировать</a>
					</span>
					<span>
						<a href="/album/{@id}/delete">Удалить</a>
					</span>
				</xsl:if>
			</div>
		</div>
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
