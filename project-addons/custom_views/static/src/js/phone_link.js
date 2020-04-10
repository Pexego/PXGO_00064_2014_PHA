$("body").on('DOMSubtreeModified', ".oe_form_field.phoneLink span", function() {
    $(this).parent().children('a').remove();
    $(this).after('<a href="tel:' + $(this).text().trim() + '">' +
                  $(this).text().trim() + '</a>');
    $(this).hide();
});