//-*- coding: utf-8 -*-
//© 2018 Pharmadus I.T.
//License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

openerp.ean10 = function(instance) {
    instance.web.ListView.include({
        load_list: function() {
            var self = this;
            this._super.apply(this, arguments);
            if (this.$buttons) {
                if (this.model == 'ean13.international') {
                    this.$buttons.find('.oe_ean10_create_ean13_int')
                        .unbind('click')
                        .click(this.proxy('on_create_ean13_int'));
                }
            }
        },
        on_create_ean13_int: function () {
            var self = this;
            new instance.web.Model('ir.model.data')
                .call('xmlid_to_res_id',
                      ['ean10.create_ean13_wizard'])
                .then(function(view_data) {
                    var action = {
                        type: 'ir.actions.act_window',
                        res_model: 'create.ean13.wizard',
                        view_mode: 'form',
                        view_type: 'form',
                        views: [[view_data, 'form']],
                        target: 'new',
                    };
                    self.do_action(action);
                });
        },
    });
};
