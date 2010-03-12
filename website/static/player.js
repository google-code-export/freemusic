/*
 * Проигрыватель для Free Music Hub.
 *
 * Примерная разметка страницы:
 *
 * <html class="audio">
 *   <div class="tracklist">
 *     <div class="track">
 *       <div class="controls"/>
 *       <a class="ogg" href="..."/>
 *       <a class="mp3" href="..."/>
 *     </div>
 *   </div>
 * </html>
 *
 * Скрипт включается если на странице есть цепочка из элементов
 * .tracklist .track .controls, в противном случае ничего не
 * происходит. Обычно эти элементы фрагментами таблицы.
 *
 * Если у элемента .tracklist есть класс autostart, проигрывание
 * будет запущего автоматически.
 *
 * @author Justin Forest <justin.forest@gmail.com>
 * @copyright 2009-2010 deadchannel.ru
 * @license http://www.gnu.org/copyleft/gpl.html GPL
 * @url http://code.google.com/p/freemusic/
 */

// Проигрыватель, основанный на HTML5.
var h5p = {
	// Объект Audio(), проигрывающий музыку.
	player: null,
	// URI воспроизводимой дорожки.
	nowplaying: null,
	// Запускать ли проигрыватель автоматически?
	autostart: false,
	// Селектор для ссылки на проигрываемый файл.
	fsel: null,

	/**
	 * Инициализация проигрывателя.
	 */
	init: function () {
		this.autostart = $('.tracklist').hasClass('autostart');
		if (Modernizr.audio && (Modernizr.audio.ogg || Modernizr.audio.mp3)) {
			// Определяем, как нам выбирать дорожку.
			h5p.fsel = Modernizr.audio.ogg ? 'a.ogg' : 'a.mp3';

			p = h5p.player = new Audio();

			// Воспроизводить начинаем только когда получено достаточное количество
			// данных для непрерывного проигрывания, см:
			// https://developer.mozilla.org/En/Using_audio_and_video_in_FireFox#Media_events
			p.addEventListener('canplaythrough', h5p.resume, true);

			// Firefox не всегда отправляет canplaythrough, когда его кэш отказывается принимать
			// больше данных, в этом случае отправляется suspend, см.
			// http://weblogs.mozillazine.org/roc/archives/2009/10/
			p.addEventListener('suspend', h5p.resume, true);

			p.addEventListener('ended', h5p.next, true);

			// В случае ошибки останавливаем воспроизведение.
			p.addEventListener('error', h5p.stop, true);

			// timeupdate не работает в хроме:
			// http://code.google.com/p/chromium/issues/detail?id=34390
			// p.addEventListener('timeupdate', h5p.on_time, true);
			setInterval(h5p.on_time, 1000);

			$('.tracklist .track .pb').click(h5p.seek);
			$('.tracklist .track .controls').html('<span/>');
			$('.tracklist .track .controls span').click(h5p.toggle);

			if (h5p.autostart)
				h5p.play(1);
		}
	},
	/**
	 * Начинает воспроизведение дорожки, содержащейся в блоке
	 * с указанным идентификатором.
	 */
	play: function (id) {
		if (id == this.nowplaying) {
			this.resume();
		} else {
			this.stop();
			this.nowplaying = id;

			$('#' + id).addClass('playing');

			// Перемотка пока отключена — мало где нормально работает.
			// $('#' + id + ' .pb').html('<div class="pb1"><div></div></div>');

			this.player.src = $('#' + id + ' ' + this.fsel).attr('href');
			this.player.load();
		}
	},
	stop: function () {
		if (h5p.player && !h5p.player.paused)
			h5p.player.pause();
		$('.tracklist .track').removeClass('playing');
		// $('.tracklist .track .pb .pb1').remove();
	},
	resume: function () {
		if (h5p.player && h5p.player.paused) {
			$('.tracklist tr:eq(' + (h5p.nowplaying-1) + ')').addClass('playing');
			h5p.player.play();
		}
	},
	next: function () {
		var n = $('#' + h5p.nowplaying + ' ~ .track:first');
		if (!n.length)
			n = $('.tracklist .track:first');
		h5p.play(n.attr('id'));
	},
	/**
	 * Вызывается при клике в кнопку play/pause.
	 */
	toggle: function () {
		var track = $(this).parents('.track:first').attr('id');
		if (h5p.nowplaying == track)
			h5p.stop();
		else {
			h5p.play(track);
		}
	},
	on_time: function () {
		if (h5p.nowplaying && h5p.player && !h5p.player.paused) {
			var pb = $('.track.playing .pb'), pos = h5p.player.currentTime / h5p.player.duration;
			var shift = 700 - (pb[0].clientWidth * pos);
			pb.css('background-position', '-' + parseInt(shift) + 'px 0px');
			// pb.html(pb.css('background-position') + '; ' + pb[0].clientWidth); // debug
		}
	},
	seek: function (e) {
		if ($(this).parents('.track:first').hasClass('playing')) {
			var x = e.pageX;
			for (p = this; p; p = p.offsetParent)
				x -= p.offsetLeft;
			try {
				if (h5p.player.duration == 'Infinity')
					alert('Seek failed: file length unknown. Retry later');
				else {
					var ct = parseInt(h5p.player.duration * x / this.clientWidth);
					h5p.player.currentTime = ct;
				}
			} catch (e) {
				h5p.msg('Перемотка в этом браузере не работает ('+ e +').');
			}
		}
	}, msg: function (text) {
		if (window.ntfctn)
			ntfctn(text);
		else
			alert(text);
	}
};

$(function(){
	if ($('.tracklist .track[id] .controls').length)
		h5p.init();
});

// vim: set ts=4 sts=4 sw=4 noet:
