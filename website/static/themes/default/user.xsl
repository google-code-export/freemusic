<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="user">
		<h2>Пользователь <xsl:value-of select="@nickname"/></h2>
		<p>Присоединился <xsl:apply-templates select="@pubDate"/>.</p>
		<img src="http://www.gravatar.com/avatar.php?gravatar_id={@hash}&amp;size=80" width="80" height="80"/>
		<xsl:if test="/page/@is-admin and not(@invited)">
			<form action="/users" method="post">
				<input type="hidden" name="email" value="{@email}"/>
				<input type="submit" value="Выслать приглашение"/>
			</form>
		</xsl:if>
	</xsl:template>
</xsl:stylesheet>
