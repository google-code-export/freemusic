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
					<xsl:with-param name="text">Метки:</xsl:with-param>
					<xsl:with-param name="uri">/?label=</xsl:with-param>
				</xsl:apply-templates>
			</div>
			<div class="right">
				<table class="tracklist">
					<tbody>
						<xsl:for-each select="tracks/track">
							<xsl:sort select="@number" data-type="number"/>
							<tr class="track" id="track-{@id}">
								<td class="r">
									<xsl:value-of select="position()"/>
									<xsl:text>.</xsl:text>
								</td>
								<td class="controls"/>
								<td class="track">
									<a href="/track/{@id}">
										<xsl:value-of select="@title"/>
									</a>
								</td>
								<td class="dl">
									<a class="ogg" href="{@ogg-link}">ogg</a>
									<xsl:text>&#160;</xsl:text>
									<a class="mp3" href="{@mp3-link}">mp3</a>
								</td>
								<td class="dur pb">
									<xsl:value-of select="@duration"/>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<p class="noaudio">Вы могли бы прослушивать музыку прямо на сайте, если бы у Вас был современный браузер, поддерживающий <a class="ext" href="http://ru.wikipedia.org/wiki/HTML5">HTML5</a> (<a href="http://chrome.google.com/" class="ext">Google Chrome</a>, <a href="http://www.getfirefox.com/" class="ext">Firefox</a> 3.5+, <a href="http://www.opera.com/" class="ext">Opera</a> 10.5+, <a href="http://www.apple.com/safari/" class="ext">Safari</a>).</p>
				<xsl:apply-templates select="../events" mode="inside"/>
				<div class="info expando">
					<h3 class="fakelink"><span>Дополнительная информация</span></h3>
					<ul>
						<li>Связаться с автором можно через пользователя, опубликовавшего это произведение: <a href="/u/{@owner}"><xsl:value-of select="@owner"/></a>.</li>
						<li>Этот альбом на других сайтах: <a href="http://www.lastfm.ru/music/{@artist-name}/{@name}" class="ext">Last.fm</a>.</li>
						<li>Плейлисты для настольных проигрывателей: <a href="/album/{@id}.mp3.pls">MP3</a>, <a href="/album/{@id}.ogg.pls">OGG</a>.</li>
					</ul>
				</div>
				<div class="reviews">
					<h3>Мнения пользователей <a class="rss" href="/album/{@id}/reviews.rss"><span>RSS</span></a></h3>
					<xsl:if test="not(../reviews/review[@author-email=/page/@email]) and /page/@logout-uri">
						<form action="/album/review" method="post">
							<input type="hidden" name="id" value="{@id}"/>
							<textarea name="comment" class="hidden">Здесь можно написать рецензию.</textarea>
							<xsl:call-template name="review-stars"/>
						</form>
					</xsl:if>
					<xsl:apply-templates select="/page/review"/>
					<xsl:if test="not(/page/reviews/review)">
						<p>
							<xsl:text>Нет ни одного мнения.</xsl:text>
							<xsl:if test="/page/@login-uri"> Чтобы оставить своё мнение, нужно <a href="{/page/@login-uri}">войти</a>.</xsl:if>
						</p>
					</xsl:if>
				</div>
			</div>
		</div>
	</xsl:template>

		<xsl:template match="events" mode="inside">
			<div class="events">
				<h3>Предстоящие концерты</h3>
				<ul>
					<xsl:for-each select="event">
						<li>
							<xsl:value-of select="concat(substring(@date,9,2),'.',substring(@date,6,2),'.',substring(@date,3,2),' ')"/>
							<a href="{@url}" class="ext">
								<xsl:value-of select="concat(@title,' @ ',@venue,' (',@city,')')"/>
							</a>
						</li>
					</xsl:for-each>
				</ul>
			</div>
		</xsl:template>

		<!-- Вывод обложки альбома. Если есть больше одной картинки,
		     выводятся скрытые уменьшеныне копии и специальная ссылка
			 для их вывода. -->
		<xsl:template match="image" mode="album-cover">
			<div class="albumcover">
				<a class="main ext" href="{@original}">
					<img src="{@medium}" alt="image" width="200" height="200"/>
				</a>
				<xsl:if test="count(../image) &gt; 1">
					<p class="moreimg fakelink"><span>Показать другие картинки</span></p>
					<ul class="moreimg hidden">
						<xsl:for-each select="../image">
							<li>
								<a href="{@original}" class="ext">
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

	<!-- Форма редактирования альбома -->
	<xsl:template match="/page/form/album">
		<div class="onecol">
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
								<input type="text" class="text" name="track.{@id}" value="{@title}"/>&#160;<a href="/track/{@id}" class="ext">#</a>
							</li>
						</xsl:for-each>
					</ol>
				</fieldset>
				<div>
					<input type="submit" value="Сохранить изменения"/> или <a href="/album/{@id}">вернуться без сохранения</a>
				</div>
			</form>
		</div>
	</xsl:template>

	<xsl:template match="album" mode="h2">
		<div class="alh">
			<div class="dlb">
				<a href="http://ru.wikipedia.org/wiki/%D0%9B%D0%B8%D1%86%D0%B5%D0%BD%D0%B7%D0%B8%D0%B8_Creative_Commons" title="Распространяется свободно" class="ext">
					<img src="http://i.creativecommons.org/l/by-sa/3.0/88x31.png" alt="Creative Commons" width="88" height="31"/>
				</a>
				<a class="button" href="{files/file/@uri}">
					<xsl:text>Скачать альбом</xsl:text>
					<xsl:if test="count(files/file) &gt; 1">
						<xsl:text> </xsl:text>
						<span class="more">▼</span>
					</xsl:if></a>
				<ul class="more popup">
					<xsl:for-each select="files/file">
						<li>
							<a href="{@uri}">
								<xsl:value-of select="@name"/>
							</a>
						</li>
					</xsl:for-each>
					<li>
						<a href="/album/{@id}/files">Показать все файлы</a>
					</li>
				</ul>
			</div>
			<h2 class="album-stars notify">
				<xsl:if test="/page/@logout-uri">
					<span title="Добавить в коллекцию">
						<xsl:attribute name="class">
							<xsl:text>star</xsl:text>
							<xsl:if test="/page/@star"> on</xsl:if>
						</xsl:attribute>
					</span>
				</xsl:if>
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
