<?xml version="1.0" encoding="utf-8"?>
<!-- vim: set ts=4 sts=4 sw=4 noet: -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:import href="default.xsl"/>

	<xsl:template match="radio">
		<div id="radio" class="onecol">
			<h2>Free Music Radio</h2>
			<p>Наше радио вещает в формате MP3, круглые сутки в случайном порядке проигрывая всю музыку, представленную на нашем сайте.&#160; Чтобы подключиться, добавьте эту ссылку в свой любимый проигрыватель:</p>
			<pre><a href="http://radio.deadchannel.ru:8000/stream.ogg">http://radio.deadchannel.ru:8000/stream.ogg</a></pre>
			<p>Возможно, у Вас заработает встроенный проигрыватель:</p>
			<embed src="http://radio.deadchannel.ru:8000/stream.ogg" width="400" height="100"/>
		</div>
	</xsl:template>
</xsl:stylesheet>
