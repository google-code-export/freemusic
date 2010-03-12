<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="radio">
		<div id="radio" class="onecol">
			<h2>Free Music Radio <small><a href="http://code.google.com/p/freemusic/wiki/Radio" class="ext">что это такое?</a></small></h2>
			<script src="http://www.gmodules.com/ig/ifr?url=http://freemusic.googlecode.com/hg/gadgets/radio/radio.xml&amp;synd=open&amp;w=280&amp;h=104&amp;border=%23ffffff%7C3px%2C1px+solid+%23999999&amp;output=js"></script>
			<div class="other">
				<div class="current"></div>
				<div class="info">
					<p>Если Вы предпочитаете настольный проигрыватель (<a href="http://ru.winamp.com/">Winamp</a>, <a href="http://www.foobar2000.org/">foobar2000</a> итд), просто добавьте в него эту ссылку:</p>
					<pre><a href="http://radio.deadchannel.ru:8000/stream.mp3">http://radio.deadchannel.ru:8000/stream.mp3</a></pre>
				</div>
			</div>
		</div>
	</xsl:template>
</xsl:stylesheet>
