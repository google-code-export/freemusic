// Скрипты для Free Music Hub.
//
// @author Justin Forest <justin.forest@gmail.com>
// @copyright 2010 deadchannel.ru
// @license http://www.gnu.org/copyleft/gpl.html GPL
// @url http://code.google.com/p/freemusic/

$(document).ready(function(){
  $('.jsonly').show();
	$('input.toggle').click(function(){
		$('.toggleMe').toggleClass('hidden');
	});
	$('#content .text:first').focus();

	$('.moreimg a').click(function(){
		var p = $(this).parents('div:first');
		$('img:first', p).attr('src', $(this).find('img').attr('src'));
		$('a:first', p).attr('href', $(this).attr('href'));
		return false;
	});

	/**
	 * Добавление альбома в закладки.
	 */
	$('.album-stars .star').click(function(){
    var id = $(this).find('a').attr('href') || window.location.pathname.split('/')[2];
    var success = $(this).parents('.album-stars:first').hasClass('notify')
      ? function (data) { ntfctn(data.notify); }
      : null;
		$(this).toggleClass('on');
		$.post('/api/album/star.json', {
			'id': id,
			'status': $(this).hasClass('on')
		}, success, 'json');
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
          ntfctn(data.message);
				else
					window.location.reload()
			},
			error: function (a, b) {
				$('.reviews input[type="submit"]').attr('disabled', '');
        ntfctn('Error ' + a.status + ': ' + a.statusText);
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
					$('#plh').append(html).slideDown('slow');
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

  /**
   * Редактирование меток альбома.
   */
  $('.edit-labels p').live('click', function(){
      var id = window.location.pathname.split('/')[2];
      $.ajax({
        type: 'GET',
        url: '/album/labels?id=' + id,
        dataType: 'json',
        success: function (data) {
          $('.edit-labels').html(data.form);
          $('.edit-labels textarea').focus();
        }
      });
  });
  $('.edit-labels form').live('submit', function(){
    $.ajax({
      type: 'POST',
      url: $(this).attr('action'),
      data: $(this).serialize(),
      dataType: 'json',
      success: function (data) {
        $('.edit-labels').html(data.html);
        if (data.notification)
          ntfctn(data.notification);
      }
    });
    return false;
  });

  $('#user-stars .labels .fakelink').click(function(){
    $('#user-stars .labels > span').toggleClass('hidden');
  });
  $('#user-stars .labels a').click(function(){
    $('#user-stars tr').hide();
    $('#user-stars .' + $(this).attr('class')).show();
    return false;
  });

  /**
   * Сохраняем информацию о скачивании, если пользователь
   * зарегистрирован, чтобы предложить написать рецензию.
   */
  $('html.auth .dlb a.file').click(function(){
    $.ajax({
      type: 'GET',
      url: '/album/download',
      data: {
        album: window.location.pathname.split('/')[2],
        file: $(this).attr('href'),
      },
    });
  });
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
        ntfctn('Error ' + a.status + ': ' + a.statusText);
      }
    });
  } catch (e) { }
}

var fotimer = null;
function ntfctn(text)
{
  if (fotimer);
    clearTimeout(fotimer);
    if (text == '')
      $('#ntfctn').html('');
    else {
      $('#ntfctn').html('<p>' + text + '</p>');
      fotimer = setTimeout(function(){ $('#ntfctn p').fadeOut(5000); }, 10000);
    }
}
