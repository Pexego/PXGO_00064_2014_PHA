//-*- coding: utf-8 -*-
//© 2023 Pharmadus Botanicals <https://www.pharmadus.com>
//License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

openerp.warehouse_shipping_light = function(instance) {
    instance.web.ListView.include({
        load_list: function() {
            var self = this;
            this._super.apply(this, arguments);
            if (this.$buttons) {
                if (this.model == 'stock.expeditions') {
                    this.$buttons.find('.oe_list_add').hide();
                    this.$buttons.find('.oe_list_button_import').hide();
                    this.$buttons.find('.oe_wsl_excel_expeditions')
                        .unbind('click')
                        .click(this.proxy('on_wsl_excel_expeditions'));
                }
            }
        },
        on_wsl_excel_expeditions: function (ids) {
            var self = this;
            var ids = self.get_selected_ids();
            new instance.web.Model('stock.expeditions')
                .call('get_excel_expedition', [ids])
                .then(function(action) {
                    self.do_action(action);
                });
        },
    });
};
