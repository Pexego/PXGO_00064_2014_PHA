# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class MrpProductProduce(models.TransientModel):
    _inherit = 'mrp.product.produce'

    picking_weight = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'))
    return_weight = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'))
    tare = fields.Float(digits=dp.get_precision('Product Unit of Measure'))

    @api.multi
    def do_produce(self):
        res = super(MrpProductProduce, self).do_produce()
        if self.picking_weight or self.return_weight or self.tare:
            production_id = self.env['mrp.production'].search([
                ('final_lot_id', '=', self.lot_id.id)
            ])
            if production_id:
                production_id.write({
                    'picking_weight': self.picking_weight,
                    'return_weight': self.return_weight,
                    'tare': self.tare
                })
            return res

    def on_change_qty(self, cr, uid, ids, product_qty, consume_lines,
                      context=None):
        res = super(MrpProductProduce, self).on_change_qty(cr, uid, ids,
                                                           product_qty,
                                                           consume_lines,
                                                           context)
        products = [r[2]['product_id'] for r in res['value']['return_lines']]
        prod_obj = self.pool.get('product.product')
        product_ids = prod_obj.browse(cr, uid, products, context)
        lowest_analysis_seq = min(
            product_ids.mapped('categ_id.analysis_sequence')
        )
        raw_material_ids = product_ids.\
            with_context(a_seq=lowest_analysis_seq).\
            filtered(lambda p: p.categ_id.analysis_sequence ==
                               p._context['a_seq'])
        if len(raw_material_ids) == 1:  # Only one raw material expected
            count = 0
            qty = 0
            for r in res['value']['return_lines']:
                if r[2]['product_id'] == raw_material_ids.id:
                    qty = r[2]['product_qty']
                    count += 1
            if count == 1:  # Only one lot allowed
                for r in res['value']['consume_lines']:
                    if r[2]['product_id'] == raw_material_ids.id:
                        qty += r[2]['product_qty']
                # Weight of raw material
                production_id = self.pool.get('mrp.production').browse(cr, uid,
                    context.get('active_id'), context=context)
                res['value']['picking_weight'] = qty \
                    if not production_id.picking_weight \
                    else production_id.picking_weight
        return res

    @api.multi
    def action_calculate_consumption(self):
        self.ensure_one()
        # Search for material with the lowest analysis sequence index
        lowest_analysis_seq = min(
            self.return_lines.mapped('product_id.categ_id.analysis_sequence')
        )
        return_line = self.return_lines.\
            with_context(a_seq=lowest_analysis_seq).\
            filtered(lambda l: l.product_id.categ_id.analysis_sequence == l._context['a_seq'])
        if len(return_line) == 1:
            consume_line = self.consume_lines.search([
                ('produce_id', '=', self.id),
                ('product_id', '=', return_line.product_id.id),
                ('lot_id', '=', return_line.lot_id.id)
            ])
            picking_total = consume_line.product_qty + return_line.product_qty
            return_line.product_qty = picking_total - self.picking_weight + \
                self.return_weight + self.tare
            self.onchange_return_lines()
            return {
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': self._name,
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        else:
            return {
                'warning': {
                    'title': _('Atención'),
                    'message': _('The calculations cannot be made with more '
                                 'than one raw material...')
                }
            }
