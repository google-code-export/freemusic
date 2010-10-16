$(document).ready(function(){
  $('a.external').attr('target', '_blank');
  $('a[href*="://"]:not([href^="'+ fmh.system.url +'"])').attr('target', '_blank').addClass('external');
});
