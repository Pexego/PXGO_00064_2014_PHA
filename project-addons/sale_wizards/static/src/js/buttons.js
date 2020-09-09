// -*- coding: utf-8 -*-
// © 2020 Pharmadus I.T.
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

openerp.sale_wizards = function(instance) {
    instance.web.ListView.include({
        load_list: function() {
            var self = this;
            this._super.apply(this, arguments);
            if (this.$buttons) {
                if (this.model == 'sale.from.catalog.items') {
                    this.$buttons.find('.oe_list_add').hide();
                    this.$buttons.find('.oe_alternative').hide();
                    this.$buttons.find('.oe_list_save')
                        .click(this.proxy('on_sale_from_catalog'));
                } else if (this.model == 'sale.from.history.items') {
                    this.$buttons.find('.oe_list_add').hide();
                    this.$buttons.find('.oe_alternative').hide();
                    this.$buttons.find('.oe_list_save').show()
                        .click(this.proxy('on_sale_from_history'));
                }
            }
        },
        on_sale_from_catalog: function() {
            var self = this;
            var ids = this.dataset.ids;

            new instance.web.Model('sale.from.catalog.items')
                .call('action_create_sale_items', [ids]).then(function(data) {
                    if (data.result == 'OK') {
                        $('.oe_breadcrumb_title a.oe_breadcrumb_item:contains("SO")').last().click();
                    }
                });
        },
        on_sale_from_history: function() {
            var self = this;
            var ids = self.get_selected_ids();

            new instance.web.Model('sale.from.history.items')
                .call('action_create_sale_items', [ids]).then(function(data) {
                    if (data.result == 'OK') {
                        $('.oe_breadcrumb_title a.oe_breadcrumb_item:contains("SO")').last().click();
                    }
                });
        },
    });
};
