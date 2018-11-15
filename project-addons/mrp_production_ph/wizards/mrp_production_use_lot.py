# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class MrpProductionAvailableLot(models.Model):
    _name = 'mrp.production.available.lot'
    _inherit = 'stock.production.lot'
    _auto = False
    _table = 'stock_production_lot'

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = rec.name + ' - ' + \
                   rec.product_id.name if rec.product_id else '( --- )'
            res.append((rec.id, name))
        return res


class MrpProductionUseLot(models.TransientModel):
    _name = 'mrp.production.use.lot'

    production_id = fields.Many2one(comodel_name='mrp.production')
    lot_id = fields.Many2one(comodel_name='mrp.production.available.lot',
        string='Lot')
    use_date = fields.Datetime(related='lot_id.use_date', readonly=True)
    duration_type = fields.Selection(selection=[
            ('exact', 'Exact'),
            ('end_month', 'End of month'),
            ('end_year', 'End of year')
        ], related='lot_id.duration_type', readonly=True)

    @api.multi
    def action_use_lot(self):
        self.ensure_one()
        lot_id = self.production_id.final_lot_id.create({
            'name': self.lot_id.name,
            'product_id': self.production_id.product_id.id,
            'quantity': self.production_id.product_qty,
            'uom_id': self.production_id.product_uom.id,
            'use_date': self.use_date,
            'duration_type': self.duration_type
        })
        self.production_id.final_lot_id = lot_id
        return True
