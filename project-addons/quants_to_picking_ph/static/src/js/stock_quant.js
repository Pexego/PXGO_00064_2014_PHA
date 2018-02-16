//-*- coding: utf-8 -*-
//© 2017 Pharmadus I.T.
//License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

openerp.quants_to_picking_ph = function(instance) {
    instance.web.ListView.include({
        load_list: function() {
            var self = this;
            this._super.apply(this, arguments);
            if (this.$buttons) {
                if (this.model == 'stock.quant') {
                    this.$buttons.find('.oe_quants_to_picking')
                        .unbind('click')
                        .click(this.proxy('on_quants_to_picking'));
                }
            }
        },
        on_quants_to_picking: function () {
            var self = this;
            var ids = self.get_selected_ids();
            var _t = instance.web._t;

            if (ids.length == 0) {
                alert(_t('You have not selected any quant!'));
            } else {
                new instance.web.Model('stock.quant')
                    .call('quants_to_picking', [ids])
                    .then(function(data) {
                        new instance.web.Model('ir.model.data')
                            .call('xmlid_to_res_id',
                                  ['quants_to_picking_ph.picking_select_dest_wizard'])
                            .then(function(view_data) {
                                var action = {
                                    type: 'ir.actions.act_window',
                                    res_model: 'quants.to.picking.wizard',
                                    view_mode: 'form',
                                    view_type: 'form',
                                    views: [[view_data, 'form']],
                                    target: 'new',
                                    context: {
                                        'default_picking_id': data.picking_id,
                                        'default_location_dest_id': data.location_dest_id
                                    },
                                };
                                self.do_action(action);
                            });
                    });
            };
        },
    });
};
