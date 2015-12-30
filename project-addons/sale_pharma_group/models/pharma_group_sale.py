# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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

from openerp import models, fields
import openerp.addons.decimal_precision as dp


class PharmaGroupSale(models.Model):

    _name = "pharma.group.sale"
    _description = "Pharma groups sales"
    _rec_name = "pharmacy_name"

    pharmacy_name = fields.Char('Pharmacy', size=255, required=True)
    pharmacy_street = fields.Char('Pharmacy street', size=255)
    pharmacy_zip = fields.Char('Zipcode', size=8, required=True)
    pharmacy_location = fields.Char('Location', size=128)
    product_cn = fields.Char('CN', size=12, required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Float('Qty.', digits=(16, 2), required=True)
    agent_id = fields.Many2one('sale.agent', 'Agent', required=True)
    price_unit = fields.Float('Price unit', required=True,
                              digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Float('Subtotal', required=True, digits=(16, 2))
    settled = fields.Boolean('Settled', readonly=True)
    settled_qty = fields.Float('Settled qty.',  digits=(16, 2), readonly=True)
    date = fields.Date('Import date')
    partner_id = fields.Many2one('res.partner', 'Partner')

    def get_applicable_commission(self):
        if self.partner_id:
            partner_agent = self.partner_id.commission_ids.filtered(
                lambda record: record.agent_id.id == self.agent_id.id)
            if partner_agent:
                return partner_agent.commission_id
        return self.agent_id.commission_id
