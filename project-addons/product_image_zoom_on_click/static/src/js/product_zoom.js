(function() {
    var instance = openerp;
    instance.web.form.FieldBinaryImage = instance.web.form.FieldBinaryImage.extend({
        template: 'FieldBinaryImage',
        render_value: function() {
            this._super();

            if (this.$('div.magnifying_glass').length == 0) {
                this.$('img').after('<div class="magnifying_glass"/>');
            };
        },
        events: {
            'mouseup div.magnifying_glass': 'zoomImage',
        },
        zoomImage: function() {
            var url = this.$('img').attr('src');
            var pos = url.indexOf('image_medium');
            if (pos != -1) {
                url = url.slice(0, pos + 5);
            };
            var image = $('<img class="zoomedImg" src="' + url + '" onclick="$(this).remove();"/>');
            $('div.openerp_webclient_container').append(image);
            image.fadeIn(200);
        },
    });
})();