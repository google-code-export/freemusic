<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="radio">
		<div id="radio" class="onecol">
			<h2>Free Music Radio <small><a href="http://code.google.com/p/freemusic/wiki/Radio" class="ext">что это такое?</a></small></h2>
			<!--
			<p>Наше радио вещает в формате MP3, круглые сутки в случайном порядке проигрывая всю музыку, представленную на нашем сайте.</p>
			-->
			<script src="http://www.gmodules.com/ig/ifr?url=http://freemusic.googlecode.com/hg/gadgets/radio/radio.xml&amp;synd=open&amp;w=280&amp;h=104&amp;border=%23ffffff%7C3px%2C1px+solid+%23999999&amp;output=js"></script>

			<!--
			<object type="application/x-shockwave-flash" width="299" height="111" data="/static/player.swf?file=http%3A%2F%2Fradio.deadchannel.ru%3A8000%2Fstream.mp3&amp;width=299&amp;height=111&amp;controlbar=none&amp;link=http://radio.deadchannel.ru/&amp;image=/static/logo.radio.png&amp;type=sound&amp;duration=-1">
			  <param name="movie" value="http://radio.deadchannel.ru:8000/stream.mp3" />
			  <param name="wmode" value="transparent" />
			</object>
			-->
			<div class="other">
				<p>Если Вы предпочитаете настольный проигрыватель (<a href="http://ru.winamp.com/">Winamp</a>, <a href="http://www.foobar2000.org/">foobar2000</a> итд), просто добавьте в него эту ссылку:</p>
				<pre><a href="http://radio.deadchannel.ru:8000/stream.mp3">http://radio.deadchannel.ru:8000/stream.mp3</a></pre>
			</div>
		</div>
	</xsl:template>
</xsl:stylesheet>
