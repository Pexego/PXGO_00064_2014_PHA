# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class LotCopyAnalysisToItems(models.TransientModel):
    _name = 'lot.copy.analysis.to.items'

    wizard_id = fields.Many2one('lot.copy.analysis.to.wizard')
    wizard_filter_id = fields.Integer()
    name = fields.Char(readonly=True)
    lot_id = fields.Many2one('stock.production.lot', readonly=True)


class LotCopyAnalysisToWizard(models.TransientModel):
    _name = 'lot.copy.analysis.to.wizard'

    origin_lot_id = fields.Many2one('stock.production.lot',
                                    'Origin lot',
                                    readonly=True)
    item_ids = fields.One2many(comodel_name='lot.copy.analysis.to.items',
                               inverse_name='wizard_id',
                               string='Destination lots')

    @api.model
    def create(self, vals):
        res = super(models.TransientModel, self).create(vals)
        qc_reception_id = self.env.ref('__export__.stock_location_14')
        lot_ids = self.env['stock.quant'].search([
            ('location_id', '=', qc_reception_id.id),
            ('lot_id', '!=', vals['origin_lot_id']),
        ]).mapped('lot_id').sorted(key=lambda l: l.name+'_'+l.product_id.name)
        item_ids = self.env['lot.copy.analysis.to.items']
        for lot_id in lot_ids:
            item_ids += item_ids.create({
                'wizard_filter_id': res.id,
                'lot_id': lot_id.id,
                'name': lot_id.name + ' : ' + lot_id.product_id.name
            })
        return res

    @api.multi
    def copy_analysis_to_selected_lots(self):
        for item_id in self.item_ids:
            item_id.lot_id.copy_analysis_from = self.origin_lot_id
            item_id.lot_id.action_copy_analysis_from()
