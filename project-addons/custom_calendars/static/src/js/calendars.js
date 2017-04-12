//-*- coding: utf-8 -*-
//© 2016 Therp BV <http://therp.nl>
//License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

openerp.custom_calendars = function(instance) {
    instance.web.ListView.include({
        load_list: function() {
            var self = this;
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.find('.oe_custom_calendars_create_calendar')
                    .click(this.proxy('on_custom_calendars_create_calendar'));
                this.$buttons.find('.oe_custom_calendars_set_holidays')
                    .click(this.proxy('on_custom_calendars_set_holidays'));
                this.$buttons.find('.oe_custom_calendars_fixed_shifts')
                    .click(this.proxy('on_custom_calendars_fixed_shifts'));
            }
        },
        on_custom_calendars_create_calendar: function () {
            var self = this;
            new instance.web.Model('ir.model.data')
                .call('xmlid_to_res_id',
                      ['custom_calendars.custom_calendars_create_calendar_wizard'])
                .then(function(data) {
                    var action = {
                            type: 'ir.actions.act_window',
                            res_model: 'calendar.wizard',
                            view_mode: 'form',
                            view_type: 'form',
                            views: [[data, 'form']],
                            target: 'new',
                            context: {'new_calendar': true},
                    };
                    self.do_action(action);
                });
        },
        on_custom_calendars_set_holidays: function () {
            var self = this;
            new instance.web.Model('ir.model.data')
                .call('xmlid_to_res_id',
                      ['custom_calendars.custom_calendars_holidays_wizard'])
                .then(function(data) {
                    var action = {
                            type: 'ir.actions.act_window',
                            res_model: 'calendar.wizard',
                            view_mode: 'form',
                            view_type: 'form',
                            views: [[data, 'form']],
                            target: 'new',
                            context: {},
                    };
                    self.do_action(action);
                });
        },
        on_custom_calendars_fixed_shifts: function () {
            var self = this;
            new instance.web.Model('ir.model.data')
                .call('xmlid_to_res_id',
                      ['custom_calendars.custom_calendars_fixed_shifts_wizard'])
                .then(function(data) {
                    var action = {
                            type: 'ir.actions.act_window',
                            res_model: 'calendar.wizard',
                            view_mode: 'form',
                            view_type: 'form',
                            views: [[data, 'form']],
                            target: 'new',
                            context: {},
                    };
                    self.do_action(action);
                });
        },
    });
};
