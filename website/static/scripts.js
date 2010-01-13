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
		$('.tracklist td.u').html('<u/>');
		$('.tracklist u').click(h5p.toggle);
		if (h5p.autostart)
			h5p.play(1);
	},
	play: function (idx) {
		this.stop();

		if (this.player && idx == this.nowplaying) {
			this.resume();
		} else if (idx <= this.playlist.length) {
			track = this.playlist[idx-1];
			this.nowplaying = idx;

			if (!this.player)
				this.player = new Audio();
			p = this.player;
			p.pause();

			// Воспроизводить начинаем только когда получено достаточное количество
			// данных для непрерывного проигрывания, см:
			// https://developer.mozilla.org/En/Using_audio_and_video_in_FireFox#Media_events
			p.addEventListener('canplaythrough', this.resume, true);

			// Firefox не всегда отправляет canplaythrough, когда его кэш отказывается принимать
			// больше данных, в этом случае отправляется suspend, см.
			// http://weblogs.mozillazine.org/roc/archives/2009/10/
			p.addEventListener('suspend', this.resume, true);

			p.addEventListener('ended', this.next, true);

			// В случае ошибки останавливаем воспроизведение.
			p.addEventListener('error', this.stop, true);
			p.src = Modernizr.audio.ogg ? track.ogg : track.mp3;
			p.load();
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
		if (this.nowplaying < this.playlist.length)
			this.play(this.nowplaying + 1);
	},
	toggle: function () {
		idx = $(this).parents('tr').find('td:first').html().split('.')[0];
		if (h5p.nowplaying != idx)
			h5p.play(idx);
		else
			h5p.stop();
	}
};

$(document).ready(function(){
	$('input.toggle').click(function(){
		$('.toggleMe').toggleClass('hidden');
	});
	$('#content .text:first').focus();

	if ($('.tracklist').length)
		h5p.init(window.location.pathname.split('/')[2]);
});

// vim: set ts=4 sts=4 sw=4 noet:
