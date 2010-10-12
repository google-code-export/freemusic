$(document).ready(function(){
	$('#album .download .button').click(function(){
		$('#downloads').toggleClass('hidden');
		return false;
	});
	$('#album #downloads form').submit(function(){
		$('#downloads').html('Подождите, запрос обрабатывается...');
		$.ajax({
			type: 'POST',
			url: $(this).attr('action'),
			data: $(this).serialize(),
			dataType: 'text',
			success: function (data) {
				$('#downloads').html(data);
			}
		});
		return false;
	});
});
