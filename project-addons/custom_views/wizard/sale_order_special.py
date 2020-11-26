# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class SaleOrderSpecial(models.TransientModel):
    _name = 'sale.order.special'
    _inherits = {'sale.order': 'order_id'}

    order_id = fields.Many2one(comodel_name='sale.order',
                               required=True, ondelete='cascade')
    aux_partner_id = fields.Many2one(comodel_name='res.partner',
                                     string='Cliente')
    aux_partner_invoice_id = fields.Many2one(comodel_name='res.partner',
                                     string='Dirección de factura')
    aux_partner_shipping_id = fields.Many2one(comodel_name='res.partner',
                                     string='Dirección de entrega')
    aux_notified_partner_id = fields.Many2one(comodel_name='res.partner',
                                     string='Cooperativa')
    aux_customer_payer = fields.Many2one(comodel_name='res.partner',
                                         string='Pagador')
    aux_customer_branch = fields.Char(string='Sucursal')
    aux_customer_department = fields.Char(string='Departamento')
    aux_customer_transmitter = fields.Many2one(comodel_name='res.partner',
                                               string='Transmisor')

    @api.multi
    def write(self, vals):
        self.ensure_one()
        data = {}
        for key in vals:
            data[key.replace('aux_', '')] = vals[key]
        self.order_id.write(data)
        res = super(SaleOrderSpecial, self).write(vals)
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def call_special_form(self):
        rec = self.env['sale.order.special'].create({
            'order_id':                 self.id,
            'aux_partner_id':           self.partner_id.id,
            'aux_partner_invoice_id':   self.partner_invoice_id.id,
            'aux_partner_shipping_id':  self.partner_shipping_id.id,
            'aux_notified_partner_id':  self.notified_partner_id.id,
            'aux_customer_payer':       self.customer_payer.id,
            'aux_customer_branch':      self.customer_branch,
            'aux_customer_department':  self.customer_department,
            'aux_customer_transmitter': self.customer_transmitter.id
        })
        view_id = self.env.ref('custom_views.view_sale_order_special_form')

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.special',
            'view_id': view_id.id,
            'res_id': rec.id,
            'target': 'current'
        }
