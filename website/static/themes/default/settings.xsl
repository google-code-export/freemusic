<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

  <xsl:template match="/page/settings">
    <h2>Настройки</h2>
    <ul>
      <li>
        <a href="/upload/settings">Amazon S3</a>
      </li>
    </ul>
  </xsl:template>
</xsl:stylesheet>
