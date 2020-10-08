$('body').on('DOMSubtreeModified', '.oe_form_field_email a.oe_form_uri', function() {
    uri = $(this).attr('href');
    if (uri.indexOf(',') > -1) {
        $(this).attr('href', uri.replace(',', ';'));
    };
});