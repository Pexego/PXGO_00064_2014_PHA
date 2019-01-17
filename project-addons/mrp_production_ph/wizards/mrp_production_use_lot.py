# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from lxml import etree


class MrpProductionAvailableLot(models.AbstractModel):
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

    def unlink(self, cr, user, ids, context=None):
        return True

    def _drop_table(self, cr, uid, ids, context=None):
        return True


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

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False,
                        submenu=False):
        res = super(MrpProductionUseLot, self).fields_view_get(view_id=view_id,
                    view_type=view_type, toolbar=toolbar, submenu=submenu)
        context = self.env.context
        if view_type == 'form' and res['model'] == 'mrp.production.use.lot' and \
                context.get('active_id'):
            # Active production
            production_id = self.env['mrp.production'].\
                browse(context.get('active_id'))
            # Products from Bill Of Materials with established analysis sequence
            product_ids = production_id.bom_id.\
                mapped('bom_line_ids.product_id').\
                filtered(lambda p: p.categ_id.analysis_sequence > 0)
            # Get products with the lowest analysis sequence
            min_sequence = min(product_ids.mapped('categ_id.analysis_sequence'))
            product_ids = product_ids.\
                filtered(lambda p: p.categ_id.analysis_sequence == min_sequence)
            # Search for available stock locations
            warehouse_id = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.user.company_id.id)])
            stock_loc_ids = warehouse_id.lot_stock_id._get_child_locations()
            # Get quants of those products that are in available stock locations
            quant_ids = self.env['stock.quant'].search([
                ('product_id', 'in', product_ids.ids),
                ('location_id', 'in', stock_loc_ids.ids)
            ])
            # Finally, obtain the desired lots
            lot_ids = quant_ids.mapped('lot_id')

            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='lot_id']"):
                if len(lot_ids) == 1:
                    domain = "[('id', '=', {})]".format(lot_ids[0].id)
                else:
                    domain = "[('id', 'in', (" + \
                             ', '.join(map(str, lot_ids.ids)) + "))]"
                node.set('domain', domain)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def action_use_lot(self):
        if self.env.context.get('add_suffix_from_lot'):
            suffix = self.lot_id.name
            aPos = [pos for pos, char in enumerate(suffix) if char == '-']
            if len(aPos) > 1:
                lot_id = self.production_id.final_lot_id
                # Using sudo() to avoid mail warnings about modified lot names
                lot_id.sudo().write({
                    'name': lot_id.name + suffix[aPos[-2]:],
                    'use_date': self.use_date,
                    'duration_type': self.duration_type
                })
            else:
                raise exceptions.Warning(_('Lot error'),
                                         _('The selected lot do not have the '
                                           'expected suffix format.'))
        else:
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
