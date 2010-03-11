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

	/**
	 * Добавление альбома в закладки.
	 */
	$('#album h2 .star').click(function(){
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

	/**
	 * Рецензии.
	 */
	$('.reviews textarea').focus(function(){
		if ($(this).hasClass('hidden'))
			$(this).html('');
		$(this).parents('.reviews:first').find('.hidden').removeClass('hidden');
		$(this).focus();
	});
	$('.reviews .star').click(function(){
		var p = $(this).parents('td:first');
		p.find('.star').removeClass('on');
		$(this).addClass('on');
		$(this).prevAll().addClass('on');
		p.find('input').val(p.find('span.on').length);
	});
	$('.reviews form').submit(function(){
		$(this).find('input[type="submit"]').attr('disabled', 'disabled');
		$.ajax({
			type: 'POST',
			url: '/album/review',
			data: $(this).serialize(),
			dataType: 'json',
			success: function (data) {
				if (data.message)
					alert(data.message);
				else
					window.location.reload()
			},
			error: function (a, b) {
				$('.reviews input[type="submit"]').attr('disabled', '');
				alert('Error ' + a.status + ': ' + a.statusText);
			}
		});
		return false;
	});

	/**
	 * Вывод дополнительных картинок альбома.
	 */
	$('p.fakelink').click(function(){
		$('.moreimg').toggleClass('hidden');
		$(this).remove();
	});

	/**
	 * Выбор файлов для скачивания.
	 */
	$('.dlb span.more').click(function(){
		var o = $(this).offset();
		var p = $('.dlb ul.more');
		p.css({
			'display': 'block',
			'left': (o.left - p.width()) + 'px',
			'top': (o.top + 4) + 'px'
		});
		return false;
	});

	/**
	 * Удаление дефолтного текста из полей.
	 */
	$('.clearme').focus(function(){
		$(this).val('');
		$(this).removeClass('clearme');
	});

	/**
	 * Сокрытие всплывающих меню при клике мимо.
	 */
	$(document).click(function(){
		$('.popup').hide();
	});

	/**
	 * Раскрываемые информационные блоки.
	 */
	$('.expando .fakelink').click(function(){
		$(this).removeClass('fakelink');
		$(this).parents('.expando:first').removeClass('expando');
	});

	$('.search .text').focus(function(){
		if ($('#plh:hidden').length) {
			$.ajax({
				url: '/labels',
				dataType: 'xml',
				success: function (data) {
					var html = '';
					$(data).find('label').each(function(){
						var l = $(this);
						html += ' <a class="weight' + l.attr('weight') + '" href="/?label='+ l.attr('uri') +'">' + l.text() + '</a>';
					});
					$('#plh').append(html).show('slow');
				}
			});
		}
	});

	/**
	 * Открытие внешних ссылок в новой вкладке.
	 */
	$('a.ext').attr('target', '_blank');

	/**
	 * Вывод случайного текстового фрагмента.
	 */
  if ($('#index').length) {
    $.ajax({
      type: 'GET',
      url: '/clips/recent.xml',
      dataType: 'html',
      success: function (clips) {
        $('#ntfctn').html('<div id="clip"><span title="Другое сообщение" class="c">⟳</span>' + clips + '</div>');
        $('#clip .ext').attr('target', '_blank');
        $('#clip li:first').show();
        $('#clip .c').click(function(){
          var n = $('#clip li:visible').next();
          if (!n.length)
            n = $('#clip li:first');
          $('#clip li').hide();
          n.show();
        });
      }
    });
  }

  /**
   * Проигрыватель для коллекции.
   */
  $('#player ul.artists input:checkbox').change(function(){
    var v = $(this).attr('checked');
    $('#player ul :checkbox:hidden').attr('checked', 'checked');
    $('#player ul.albums .artist-' + $(this).val()).css('display', v ? 'block' : 'none');
    $('#player .ptl .artist-' + $(this).val()).css('display', v ? 'table-row' : 'none');
  });
  $('#player ul.albums input:checkbox').change(function(){
    var v = $(this).attr('checked') ? 'table-row' : 'none';
    $('#player .ptl .album-' + $(this).val()).css('display', v);
  });

  /**
   * Вывод играющей на радио дорожки.
   */
  if ($('#radio').length)
    radio_np();
});

// Идентфикатор интервала, чтобы установить только один раз.
var radio_np_iid = null;

function radio_np()
{
  try {
    $.ajax({
      type: 'GET',
      url: '/radio/current.json',
      dataType: 'json',
      success: function (data) {
        $('#radio .current').html('<p>Сейчас проигрывается: ' + data.html + '.</p>');
        if (!radio_np_iid)
          radio_np_iid = setInterval(radio_np, data.ttl * 1000);
      }, error: function (a, b) {
				alert('Error ' + a.status + ': ' + a.statusText);
      }
    });
  } catch (e) { }
}
