// Скрипты для Free Music Hub.
//
// @author Justin Forest <justin.forest@gmail.com>
// @copyright 2010 deadchannel.ru
// @license http://www.gnu.org/copyleft/gpl.html GPL
// @url http://code.google.com/p/freemusic/

// Проигрыватель, основанный на HTML5.
var h5p = {
	playlist: null,
	player: null,
	nowplaying: null,
	autostart: false,
	init: function (album_id) {
		if (window.location.href.indexOf('?play') > 0)
			this.autostart = true;
		if (Modernizr.audio && (Modernizr.audio.ogg || Modernizr.audio.mp3)) {
			$.getJSON('/api/album/tracks.json?id=' + album_id, this.on_playlist);
		}
	},
	on_playlist: function (data) {
		h5p.playlist = data;

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

		p.addEventListener('timeupdate', h5p.on_time, true);

		$('.tracklist td.track').append('<div><div class="prg"></div></div>');
		$('.tracklist td.track > div').click(h5p.seek);

		$('.tracklist td.u').html('<u/>');
		$('.tracklist u').click(h5p.toggle);
		if (h5p.autostart)
			h5p.play(1);
	},
	play: function (idx) {
		if (idx == this.nowplaying) {
			this.resume();
		} else if (idx <= this.playlist.length) {
			this.stop();

			track = this.playlist[idx-1];
			this.nowplaying = idx;

			this.player.src = Modernizr.audio.ogg ? track.ogg : track.mp3;
			this.player.load();
		}
	},
	stop: function () {
		if (h5p.player && !h5p.player.paused)
			h5p.player.pause();
		$('.tracklist tr').removeClass('playing');
	},
	resume: function () {
		if (h5p.player && h5p.player.paused) {
			$('.tracklist tr:eq(' + (h5p.nowplaying-1) + ')').addClass('playing');
			h5p.player.play();
		}
	},
	next: function () {
		h5p.play(h5p.nowplaying < h5p.playlist.length ? h5p.nowplaying + 1 : 1);
	},
	toggle: function () {
		idx = parseInt($(this).parents('tr').find('td:first').html().split('.')[0]);
		if (h5p.nowplaying != idx || (h5p.player && h5p.player.paused))
			h5p.play(idx);
		else
			h5p.stop();
	},
	on_time: function () {
		pos = h5p.player.currentTime * 100 / h5p.player.duration;
		div = $('.tracklist tr:eq('+ (h5p.nowplaying-1) +') .prg');
		div.css('width', parseInt(pos) + '%');
	},
	seek: function (e) {
		var x = e.pageX;
		for (p = this; p; p = p.offsetParent)
			x -= p.offsetLeft;
		h5p.player.currentTime = h5p.player.duration * x / this.clientWidth;
	}
};

$(document).ready(function(){
	$('input.toggle').click(function(){
		$('.toggleMe').toggleClass('hidden');
	});
	$('#content .text:first').focus();

	if ($('.tracklist').length)
		h5p.init(window.location.pathname.split('/')[2]);

	$('.moreimg a').click(function(){
		var p = $(this).parents('div:first');
		$('img:first', p).attr('src', $(this).find('img').attr('src'));
		$('a:first', p).attr('href', $(this).attr('href'));
		return false;
	});

	$('#album .star').click(function(){
		$(this).toggleClass('on');
		$.post('/api/album/star.json', {
			'id': window.location.pathname.split('/')[2],
			'status': $(this).hasClass('on')
		}, function (data) {
			if (data.notify)
				$('#ntfctn').html('<p>Альбом добавлен в <a href="/my/collection">коллекцию</a>.&nbsp; <a href="http://code.google.com/p/freemusic/wiki/Collection" target="_blank">Подробнее</a></p>');
			else
				$('#ntfctn').html('');
		}, 'json');
	});
});

// vim: set ts=4 sts=4 sw=4 noet:
