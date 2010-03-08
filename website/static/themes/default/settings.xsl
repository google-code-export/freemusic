<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

  <xsl:template match="/page/settings">
    <h2>Настройки</h2>
    <ul>
      <li>
        <a href="/settings/s3">Amazon S3</a>
      </li>
    </ul>

	<form method="post" class="gen">
		<div>
			<label>
				<span>Модератор альбомов:</span>
				<input type="text" name="album_moderator" value="{@album_moderator}"/>
			</label>
		</div>
		<div>
			<input type="submit"/>
		</div>
	</form>
  </xsl:template>
</xsl:stylesheet>
