var playlist = null, player = null, nowplaying = null;

$(document).ready(function(){
	$('input.toggle').click(function(){
		$('.toggleMe').toggleClass('hidden');
	});
	$('#content .text:first').focus();

	$('#content .right .player').each(function(){
		var player = $(this);
		if (Modernizr.audio && (Modernizr.audio.ogg || Modernizr.audio.mp3)) {
			$('table td.u').html('<u/> ');
			$.getJSON('/api/album/tracks.json?id=' + window.location.pathname.split('/')[2], function (data) {
				window.playlist = data;
				// Добавление к адресу страницы ?play вызывает автозапуск проигрывателя.
				if (window.location.href.indexOf('?play') > 0)
					play_album_track(1);
			});
		}
	});

	$('.tracklist u').click(function(){
		var tr = $(this).parents('tr');
		if (tr.hasClass('playing')) {
			tr.removeClass('playing');
			player.pause();
		} else {
			play_album_track(tr.find('td:first').html().split('.')[0]);
		}
	});
});

function play_album_track(idx)
{
	$('table.tracklist tr').removeClass('playing');
	$('table.tracklist tr:eq(' + (idx-1) + ')').addClass('playing');

	if (player && idx == nowplaying) {
		player.play();
	} else {
		track = playlist[idx-1];
		nowplaying = idx;

		if (!player)
			player = new Audio();
		player.pause();

		// Воспроизводить начинаем только когда получено достаточное количество
		// данных для непрерывного проигрывания, см:
		// https://developer.mozilla.org/En/Using_audio_and_video_in_FireFox#Media_events
		player.addEventListener('canplaythrough', start_playing_track, true);

		// Firefox не всегда отправляет canplaythrough, когда его кэш отказывается принимать
		// больше данных, в этом случае отправляется suspend, см.
		// http://weblogs.mozillazine.org/roc/archives/2009/10/
		player.addEventListener('suspend', start_playing_track, true);

		// В случае ошибки останавливаем воспроизведение.
		player.addEventListener('error', function(){
			if (!this.paused)
				this.pause();
			$('table.tracklist tr').removeClass('playing');
		}, true);
		player.src = Modernizr.audio.ogg ? track.ogg : track.mp3;
		player.load();
	}
}

function start_playing_track()
{
	if (this.paused) {
		this.play();
		// По окончанию запускаем следующую дорожку.
		if (nowplaying < playlist.length) {
			this.addEventListener('ended', function(){
				play_album_track(parseInt(nowplaying) + 1);
			}, true);
		}
	}
}

// vim: set ts=4 sts=4 sw=4 noet:
