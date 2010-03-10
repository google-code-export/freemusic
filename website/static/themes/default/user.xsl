<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="user">
		<h2>Профиль пользователя <xsl:value-of select="@nickname"/></h2>
		<div id="profile">
			<img src="http://www.gravatar.com/avatar.php?gravatar_id={@hash}&amp;size=80" width="80" height="80"/>
			<ul>
				<li><a href="/reviews?author={@nickname}">Рецензии</a></li>
				<li><a href="/player?user={@nickname}">Коллекция</a></li>
				<li>На сайте с <xsl:apply-templates select="@pubDate"/></li>
			</ul>
		</div>
	</xsl:template>
</xsl:stylesheet>
