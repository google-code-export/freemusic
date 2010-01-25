<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="labels">
		<div class="onecol">
			<h2>Метки</h2>
			<xsl:apply-templates select="." mode="linked">
				<xsl:with-param name="uri">/?label=</xsl:with-param>
			</xsl:apply-templates>
		</div>
	</xsl:template>
</xsl:stylesheet>
