$("body").on('DOMSubtreeModified', ".oe_form_field.phoneLink span", function() {
    $(this).replaceWith('<a href="tel:' + $(this).text().trim() + '">' +
                        $(this).text().trim() + '</a>');
});