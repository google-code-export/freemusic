$(function(){
	var playrow = function (row) {
		var sel;
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
				row.parents('table:first').find('tr').removeClass('np');
				row.addClass('np');
				return true;
			}
		}
	}

	$('#album #tracklist tr .l a').click(function(){
		if (Modernizr.audio)
			return !playrow($(this).parents('tr:first'));
	});

	$('html.audio #player audio').each(function(){
		$(this).bind('ended', function () {
			var next = $('#tracklist tr.np ~ tr');
			if (!next.length)
				next = $('#tracklist tr:first');
			playrow(next);
		});
	});
});
