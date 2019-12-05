$("body").on('DOMSubtreeModified', ".oe_form_field.phoneLink", function() {
    $(this).replaceWith('<a href="tel:' + $(this).text().trim() + '">' +
                        $(this).text().trim() + '</a>');
});