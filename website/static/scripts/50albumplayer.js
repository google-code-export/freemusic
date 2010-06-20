$(function(){
	$('#album #tracklist tr .l a').click(function(){
		if (Modernizr.audio) {
			var row = $(this).parents('tr:first'), link, sel;
			if (Modernizr.audio.ogg)
				sel = '.ogg';
			else if (Modernizr.audio.mp3)
				sel = '.mp3';
			if (sel) {
				var link = row.find(sel).attr('href');
				if (link) {
					var player = $('#album audio')[0];
					player.src = link;
					player.play();
					$(this).parents('table:first').find('tr').removeClass('np');
					row.addClass('np');
					return false;
				}
			}
		}
	});

	$('html.audio #player audio').each(function(){
		$(this).bind('ended', function () {
			$('#tracklist tr').removeClass('np');
		});
	});
});
