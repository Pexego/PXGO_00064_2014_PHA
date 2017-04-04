# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    default_code = fields.Char(related='product_id.default_code')
    qty_available = fields.Float(related='product_id.qty_available')
    virtual_available = fields.Float(related='product_id.virtual_available')
    virtual_conservative = fields.Float(related='product_id.virtual_conservative')
    stock_by_day_i = fields.Float(related='product_id.stock_by_day_i')
    stock_by_day_p = fields.Float(related='product_id.stock_by_day_p')
    cons_by_day_i = fields.Float(related='product_id.cons_by_day_i')
    cons_by_day_p = fields.Float(related='product_id.cons_by_day_p')
