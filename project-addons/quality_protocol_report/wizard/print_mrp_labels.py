# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _


class PrintMrpLabels(models.TransientModel):

    _name = 'print.mrp.labels'

    production_id = fields.Many2one('mrp.production', 'Production')
    product_id = fields.Many2one('product.product', related='production_id.product_id')
    gtin = fields.Many2one('product.gtin14')

    @api.model
    def default_get(self, fields):
        res = super(PrintMrpLabels, self).default_get(fields)
        mrp = self.env[self._context.get('active_model', False)].browse(
            self._context.get('active_id', False))
        res['production_id'] = mrp.id
        res['gtin'] = mrp.product_id.gtin14_default.id

        return res

    @api.multi
    def print_labels(self):
        if not self.production_id.final_lot_id:
            raise exceptions.Warning(_('Lot error'), _('Confirma la producción para que le asigne el lote final'))
        self.ensure_one()
        datas = {'ids': [self.production_id.id],
                 'gtin': self.gtin.gtin14,
                 'box_elements': self.gtin.units}
        return self.env['report'].get_action(
            self.production_id, 'quality_protocol_report.report_mrp_label', data=datas)

    @api.multi
    def print_tiny_labels(self):
        if not self.production_id.final_lot_id:
            raise exceptions.Warning(_('Lot error'), _('Confirma la producción para que le asigne el lote final'))
        self.ensure_one()
        datas = {'ids': [self.production_id.id],
                 'gtin': self.gtin.gtin14,
                 'box_elements': self.gtin.units}
        return self.env['report'].get_action(
            self.production_id, 'quality_protocol_report.report_mrp_tiny_label', data=datas)
