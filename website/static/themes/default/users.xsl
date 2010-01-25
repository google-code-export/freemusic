<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="userlist">
		<div class="onecol">
			<h2>Список пользователей</h2>
			<form method="post">
				<table>
					<tbody>
						<xsl:for-each select="user">
							<xsl:sort select="@email"/>
							<tr>
								<xsl:if test="/page/@is-admin">
									<td>
										<xsl:if test="not(@invited)">
											<input type="checkbox" name="email" value="{@email}"/>
										</xsl:if>
									</td>
								</xsl:if>
								<td>
									<xsl:value-of select="@email"/>
								</td>
							</tr>
						</xsl:for-each>
					</tbody>
				</table>
				<input type="submit" name="invite" value="Пригласить"/>
			</form>
		</div>
	</xsl:template>
</xsl:stylesheet>
