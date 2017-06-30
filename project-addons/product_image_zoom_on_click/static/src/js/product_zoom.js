$(document).ready(function () {
    $(document).on('click', 'span.image_zoom', function(e){
        var url = $(this).children('img').attr('src');
        var pos = url.indexOf('image_medium');
        url = url.slice(0, pos + 5);
        var image = '<img class="zoomedImg" src="' + url + '" onclick="$(this).remove();"/>'
        $('div.openerp_webclient_container').append(image);
    });
});
