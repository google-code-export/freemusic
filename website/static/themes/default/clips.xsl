<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="clips">
		<div id="clips">
			<h2>Фрагменты</h2>
			<xsl:if test="clip">
				<table>
					<tbody>
						<xsl:for-each select="clip">
							<tr>
								<td>
									<xsl:value-of select="text()"/>
									<xsl:if test="@url">
										<xsl:text> </xsl:text>
										<a href="{@url}" class="ext">Подробнее…</a>
									</xsl:if>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
			</xsl:if>
			<form method="post" action="/clips">
				<textarea name="text" class="text"></textarea> <span class="help">Текст</span>
				<div>
					<input type="text" name="url" class="text"/> <span class="help">URL (не обязательно)</span>
				</div>
				<div>
					<input type="submit" value="Добавить"/>
				</div>
			</form>
		</div>
	</xsl:template>
</xsl:stylesheet>
