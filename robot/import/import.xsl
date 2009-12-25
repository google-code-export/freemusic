<?xml version="1.0"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output
		method="xml"
		version="1.0"
		encoding="utf-8"
		indent="yes"
		/>

	<xsl:variable name="base">http://ebm.net.ru/</xsl:variable>

	<xsl:template match="/nodes">
		<data>
			<xsl:apply-templates select="node[@class='artist']">
				<xsl:sort select="@name"/>
			</xsl:apply-templates>
		</data>
	</xsl:template>

	<xsl:template match="node[@class='artist']">
		<artist name="{@name}">
			<xsl:variable name="artist" select="@name"/>
			<xsl:apply-templates select="/nodes/node[@class='release' and artist/node/@name=$artist]">
				<xsl:sort select="@created"/>
				<xsl:with-param name="artist" select="@name"/>
			</xsl:apply-templates>
		</artist>
	</xsl:template>

	<xsl:template match="node[@class='release']">
		<xsl:param name="artist"/>
		<xsl:document href="album-{@id}.xml" method="xml" encoding="utf-8" indent="yes">
			<album artist="{$artist}" name="{@name}" pubDate="{date/text()}">
				<xsl:apply-templates select="picture"/>
				<tracks>
					<xsl:apply-templates select="files/node[filetype/text()='audio/mpeg']"/>
				</tracks>
				<xsl:variable name="files" select="files/node[not(contains(filetype/text(),'image/')) and not(contains(filetype/text(),'audio/'))]" mode="downloadable"/>
				<xsl:if test="$files">
					<files>
						<xsl:for-each select="$files">
							<file
								name="{@name}"
								uri="{$base}{download-url/text()}"
								type="{filetype/text()}"
								size="{filesize/text()}"
								/>
						</xsl:for-each>
					</files>
				</xsl:if>
			</album>
		</xsl:document>
	</xsl:template>

	<xsl:template match="picture">
		<images>
			<image uri="{concat($base,@url)}" width="{@width}" height="{@height}" type="original"/>
			<xsl:for-each select="version">
				<image uri="{$base}{@url}" width="{@width}" height="{@height}" type="{@name}"/>
			</xsl:for-each>
		</images>
	</xsl:template>

	<xsl:template match="node[filetype/text()='audio/mpeg']">
		<track title="{@name}" number="{position()}" mp3="{$base}{download-url/text()}" mp3-length="{filesize/text()}" duration="{metadata/duration/text()}"/>
	</xsl:template>
</xsl:stylesheet>
