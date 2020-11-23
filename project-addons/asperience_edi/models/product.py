# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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

from openerp import api, models, fields


class ProductProduct(models.Model):

    _inherit = "product.product"

    ean14 = fields.Char("EAN 14")

    @api.multi
    def get_customer_info(self, partner_id):
        self.ensure_one()
        customer_info = self.customer_ids.filtered(lambda r: r.name.id == partner_id)
        if len(customer_info) > 1:
            customer_info = customer_info[0]
        return customer_info.product_code

    @api.multi
    def create_edi_customer_info(self, partner_id, reference):
        self.env["product.supplierinfo"].create(
            {
                "name": partner_id,
                "product_tmpl_id": self.product_tmpl_id.id,
                "product_code": reference,
                "type": "customer",
            }
        )

    def get_gtin14(self, partner_id):
        self.ensure_one()
        use_gtin = self.gtin14_ids.filtered(lambda r: partner_id in r.partner_ids._ids)
        if not use_gtin:
            use_gtin = self.gtin14_default
        return use_gtin.gtin14


class ProductUom(models.Model):

    _inherit = "product.uom"

    edi_code = fields.Char("Edi code")
