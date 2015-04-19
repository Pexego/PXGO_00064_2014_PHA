# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, exceptions, _


class product_quality_limits(models.Model):

    _name = "product.quality.limits"

    name = fields.Char('Name', size=64, required=True)
    loc_samples = fields.Integer('Loc Samples')
    weight_alert_full_from = fields.Float('From')
    weight_action_full_from = fields.Float('From')
    unit_weight = fields.Float('Unit weight')
    weight_alert_unit_from = fields.Float('From')
    weight_action_unit_from = fields.Float('From')
    weight_alert_full_to = fields.Float('To')
    weight_action_full_to = fields.Float('To')
    weight_alert_unit_to = fields.Float('To')
    weight_action_unit_to = fields.Float('To')

class product_product(models.Model):

    _inherit = 'product.product'

    protocol_ids = fields.Many2many('quality.protocol.report',
                                    'product__protocol_rel',
                                    'product_id', 'protocol_id', 'Protocols')
    protocol_count = fields.Integer('Protocols count',
                                    compute='_get_protocol_count')
    lot_label = fields.Boolean('Lot label')
    quality_limits = fields.Many2one('product.quality.limits', 'Quality limits')

    @api.one
    @api.depends('protocol_ids')
    def _get_protocol_count(self):
        self.protocol_count = len(self.protocol_ids)

    @api.one
    def create_protocols(self):
        if not self.base_form_id or not self.container_id:
            raise exceptions.except_orm(_('Protocol error'),
                                        _('to assign protocols is necessary \
                                           to establish the base form or \
                                           container'))
        for type_id in self.env['protocol.type'].search([]):
            report_ids = self.env['quality.protocol.report'].search(
                [('product_form_id', '=', self.base_form_id.id),
                 ('product_container_id', '=', self.container_id.id),
                 ('type_id', '=', type_id.id)])
            if report_ids:
                report_id = report_ids[0]
                report_id.write({'product_ids': [(4, self.id)]})

    def _get_act_window_dict(self, cr, uid, name, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.xmlid_to_res_id(cr, uid, name,
                                         raise_if_not_found=True)
        result = act_obj.read(cr, uid, [result], context=context)[0]
        return result

    def action_view_protocols(self, cr, uid, ids, context=None):
        result = self._get_act_window_dict(
            cr, uid, 'quality_protocol_report.action_quality_protocol_report',
            context=context)
        if len(ids) == 1:
            result['context'] = "{'default_product_ids': [" + str(ids[0]) + \
                "], 'search_default_product_ids': " + str(ids[0]) + "}"
        else:
            result['domain'] = "[('product_ids','in',[" + \
                ','.join(map(str, ids)) + "])]"
            result['context'] = "{}"
        return result


class ProductTemplate(models.Model):

    _inherit = "product.template"

    protocol_count = fields.Integer('Protocols count',
                                    compute='_get_protocol_count')

    @api.one
    @api.depends('product_variant_ids.protocol_ids')
    def _get_protocol_count(self):
        self.protocol_count = sum([p.protocol_count for p in
                                   self.product_variant_ids])

    def action_view_protocols(self, cr, uid, ids, context=None):
        products = self._get_products(cr, uid, ids, context=context)
        result = self._get_act_window_dict(
            cr, uid, 'quality_protocol_report.action_quality_protocol_report',
            context=context)
        if len(ids) == 1 and len(products) == 1:
            result['context'] = "{'default_product_ids': [" + \
                str(products[0]) + "], 'search_default_product_ids': " + \
                str(products[0]) + "}"
        else:
            result['domain'] = "[('product_ids','in',[" + \
                ','.join(map(str, products)) + "])]"
            result['context'] = "{}"
        return result
