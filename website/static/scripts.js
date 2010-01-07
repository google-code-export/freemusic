$(document).ready(function(){
	$('input.toggle').click(function(){
		$('.toggleMe').toggleClass('hidden');
	});
	$('#content .text:first').focus();
});

// vim: set ts=4 sts=4 sw=4 noet:
