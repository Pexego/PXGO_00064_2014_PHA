# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api
from openerp.exceptions import Warning


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    customer_notes = fields.Text()

    @api.multi
    def view_customer_notes(self):
        raise Warning(self.customer_notes)
