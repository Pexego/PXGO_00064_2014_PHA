# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    prestashop_tax_ids = fields.Char(help="comma separated ids of prestashop taxes")
    prestashop_without_taxes = fields.Boolean(help="Los pedidos sin impuestos se importarán con esta posición fiscal")
