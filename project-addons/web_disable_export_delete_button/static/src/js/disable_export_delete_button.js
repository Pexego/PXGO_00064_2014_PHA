openerp.web_disable_export_delete_button = function(instance) {
    var _t = instance.web._t;

    instance.web.Sidebar.include({
        add_items: function(section_code, items) {
            var hasExportButton = $('span#web_disable_export_delete_button').attr('user_in_export_group') == 1;
            var hasDeleteButton = $('span#web_disable_export_delete_button').attr('user_in_delete_group') == 1;

            if ((this.session.uid == 1) || (hasExportButton && hasDeleteButton)) {
                this._super.apply(this, arguments);
            } else {
                var new_items = items,
                    labelExport = _t('Export'),
                    labelDelete = _t('Delete');
                if (section_code == 'other') {
                    new_items = [];
                    for (var i = 0; i < items.length; i++) {
                        if (!hasExportButton && items[i]['label'] == labelExport) { continue; }
                        if (!hasDeleteButton && items[i]['label'] == labelDelete) { continue; }
                        new_items.push(items[i]);
                    };
                };
                if (new_items.length > 0) {
                    this._super.call(this, section_code, new_items);
                };
            }
        },
    });
};
