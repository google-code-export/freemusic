<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="/page/upload">
		<div id="aupload">
			<h2>Загрузка альбома</h2>
			<form action="http://{@worker}">
				<div>
					<input type="file" name="file"/>
				</div>
				<input type="submit"/>
			</form>
		</div>
	</xsl:template>

	<xsl:template match="upload-xml-form">
		<h2>Upload XML</h2>
		<form method="post" enctype="multipart/form-data">
			<div>
				<input type="file" name="xml"/>
			</div>
			<input type="submit"/>
		</form>
	</xsl:template>

	<xsl:template match="/page/upload-remote">
		<div class="onecol">
			<h2>Загрузка альбома с другого сайта</h2>
			<form method="post" class="gen">
				<div>
					<label>
						<span>Адрес ZIP-архива:</span>
						<input type="text" name="url" class="text"/>
					</label>
					<p class="hint">Это должна быть прямая ссылка, страницы-посредники вроде RapidShare работать не будут.</p>
					<xsl:apply-templates select="." mode="robot-status"/>
				</div>
				<input type="submit"/> или <a href="/upload">загрузить файл</a>
			</form>
		</div>
	</xsl:template>

		<xsl:template match="upload-remote|s3-upload-form" mode="robot-status">
			<xsl:choose>
				<xsl:when test="not(@robot-is-online)">
					<p class="statuserr">Робот в отключке, альбом будет обработан не сразу. Вы получите уведомление по электронной почте.</p>
				</xsl:when>
				<!--
				<xsl:otherwise>
					<p class="statusok">Робот здоров, альбом будет обработан максимально быстро.</p>
				</xsl:otherwise>
				-->
			</xsl:choose>
		</xsl:template>

	<xsl:template match="/page/queue">
		<h2>Очередь обработки</h2>
		<xsl:if test="S3File">
			<p>Здесь выводятся <a href="/upload">загруженные</a> альбомы, которые ещё не были обработаны. Наши роботы сейчас над ними работают.</p>
			<table class="basic queue">
				<thead>
					<tr>
						<th/>
						<th>№</th>
						<th>Файл</th>
						<th>Размер</th>
						<th>Владелец</th>
						<th>XML</th>
					</tr>
				</thead>
				<tbody>
					<xsl:for-each select="S3File">
						<xsl:sort select="@created"/>
						<tr>
							<td>
								<xsl:if test="@xml-uri and /page/@is-admin">
									<input type="checkbox" name="process" value="{@id}"/>
								</xsl:if>
							</td>
							<td><xsl:value-of select="@id"/>.</td>
							<td>
								<a href="{@file-uri}">
									<xsl:value-of select="@name"/>
								</a>
							</td>
							<td class="size">
								<xsl:value-of select="@size"/>
							</td>
							<td>
								<a href="/u/{@owner}">
									<xsl:value-of select="@owner"/>
								</a>
							</td>
							<td>
								<xsl:if test="@xml-uri">
									<a href="{@xml-uri}">XML</a>
								</xsl:if>
							</td>
						</tr>
					</xsl:for-each>
				</tbody>
			</table>
			<xsl:if test="/page/@is-admin and S3File[@xml-uri]">
				<button>Обработать отмеченные</button>
			</xsl:if>
		</xsl:if>
		<xsl:if test="not(S3File)">
			<p>Очередь пуста, <a href="/upload">загрузи</a> что-нибудь<a href="/upload/remote">!</a></p>
		</xsl:if>
	</xsl:template>

	<xsl:template match="s3-settings">
		<h2>Amazon S3 Settings <small><a href="/settings">more</a></small></h2>
		<form action="{@action}" method="post" class="gen">
			<div>
				<label for="s3a">Access Key:</label>
				<input id="s3a" type="text" name="s3a" value="{@s3a}" class="text"/>
			</div>
			<div>
				<label for="s3s">Secret Key:</label>
				<input id="s3s" type="text" name="s3s" value="{@s3s}" class="text"/>
			</div>
			<div>
				<label for="bucket">Bucket Name:</label>
				<input id="bucket" type="text" name="bucket" value="{@bucket}" class="text"/>
			</div>
			<!--
			<div>
				<label for="after">После загрузки переходить на:</label>
				<input id="after" type="text" name="after" value="{@after}" class="text"/>
			</div>
			-->
			<div>
				<input type="submit" value="Save" class="button"/>
			</div>
		</form>
	</xsl:template>

	<xsl:template match="s3-upload-form">
		<div class="twocol">
			<!--
			<div class="left">
				<ul>
					<li><a href="/upload">Обычная загрузка</a></li>
					<li><a href="/upload/ftp">Загрузка по FTP</a></li>
				</ul>
			</div>
			-->
			<div class="right">
				<h2>Загрузка нового альбома</h2>
				<!--
				http://docs.amazonwebservices.com/AmazonS3/2006-03-01/index.html?UsingHTTPPOST.html
				-->
				<p>Пожалуйста, подготовьте ZIP архив со всеми звуковыми файлами, картинками, буклетами и всем, что считаете нужным.&#160; Чем лучшего качества будут звуковые файлы, тем лучше; мы рекомендуем <a href="http://ru.wikipedia.org/wiki/FLAC" class="ext">FLAC</a>, WAV или AIFF (мы сами сделаем из них MP3 и OGG).</p>
				<p>После загрузки файла наши роботы примутся его обрабатывать, о результатах вам сообщат по электронной почте.</p>
				<xsl:apply-templates select="." mode="robot-status"/>
				<label><input type="checkbox" class="toggle"/> Всё понятно</label>
				<form action="http://{@bucket}.s3-external-3.amazonaws.com/" method="post" enctype="multipart/form-data" class="hidden toggleMe fileUpload">
					<input type="hidden" name="AWSAccessKeyId" value="{@access-key}"/>
					<input type="hidden" name="acl" value="public-read"/>
					<input type="hidden" name="key" value="{@key}"/>
					<input type="hidden" name="policy" value="{@policy}"/>
					<input type="hidden" name="signature" value="{@signature}"/>
					<input type="hidden" name="success_action_redirect" value="{@base}upload"/>
					<div>
						<input type="file" name="file"/>
					</div>
					<div>
						<input type="submit" value="Начать загрузку"/>
					</div>
					<p>Будет здорово, если ваш браузер умеет показывать ход загрузки.&#160; Мы рекомендуем <a href="http://www.google.com/chrome/" class="ext">Google Chrome</a>.</p>
				</form>
				<p><small>Если ZIP архив уже загружен на какой-нибудь другой веб-сервер, можно просто <a href="/upload/remote">прислать ссылку на него</a>.</small></p>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="s3-upload-ok">
		<div class="twocol">
			<div class="right">
				<h2>Загрузка завершена</h2>
				<p>Файл успешно загружен, ему присвоен <a href="/upload/queue">номер <xsl:value-of select="@file-id"/></a>.&#160; Наши роботы скоро им займутся, обо всём происходящем вам будут сообщать по электронной почте.</p>
				<p><a href="/upload">Загрузить ещё один файл</a></p>
			</div>
		</div>
	</xsl:template>

	<xsl:template match="s3-login-message">
		<div class="twocol">
			<div class="right">
				<h2>Загрузка нового альбома</h2>
				<p>Для этого вам понадобится авторизоваться.&#160; Если вы ещё не&#160;зарегистрированы в&#160;Google, вы можете без&#160;труда сделать это.</p>
				<p><a href="{/page/@login-uri}">Продолжить</a></p>
			</div>
		</div>
	</xsl:template>
</xsl:stylesheet>
