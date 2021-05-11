# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class StockLotMoveProductions(models.TransientModel):
    _name = 'stock.lot.move.productions'
    _order = 'date'

    lot_tracking_id = fields.Many2one(comodel_name='lot.tracking.productions')
    origin = fields.Char(string='Origin')
    date = fields.Datetime(string='Date')
    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product')
    lot_id = fields.Many2one(comodel_name='stock.production.lot', string='Lot')
    location_id = fields.Many2one(string='Source Location',
                                  comodel_name='stock.location')
    location_dest_id = fields.Many2one(string='Destination location',
                                       comodel_name='stock.location')
    real_consumed_qty = fields.Float()
    theoretical_produced_units = fields.Float()
    real_produced_units = fields.Float()
    theoretical_consumed_qty = fields.Float()
    stock_qty = fields.Float()

    @api.multi
    def action_show_origin(self):
        self.ensure_one()
        origin = self.origin
        if origin and origin[0:2] in ('PO', 'SO', 'MO'):
            if origin[0:2] == 'PO':
                model = 'purchase.order'
            elif origin[0:2] == 'SO':
                model = 'sale.order'
            else:
                model = 'mrp.production'

            order_id = self.env[model].search([('name', '=', origin.strip())])

            if order_id:
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': model,
                    'res_id': order_id.id,
                    'target': 'current',
                    'nodestroy': True,
                    'context': self.env.context
                }


class LotTrackingProductions(models.Model):
    _name = 'lot.tracking.productions'
    _rec_name = 'product_id'
    _order = 'date_received'

    product_id = fields.Many2one(comodel_name='product.product',
                                 domain="[('sequence_id', '!=', False)]",
                                 string='Product')
    lot_id = fields.Many2one(comodel_name='stock.production.lot',
                             domain="[('product_id', '=', product_id)]",
                             string='Lot')
    supplier_id = fields.Many2one(comodel_name='res.partner', readonly=True,
                                  string='Supplier')
    date_received = fields.Date(readonly=True)
    supplier_lot = fields.Char(readonly=True)
    qty_received = fields.Float(readonly=True)
    lot_move_ids = fields.One2many(comodel_name='stock.lot.move.productions',
                                   inverse_name='lot_tracking_id',
                                   readonly=True)
    harnessing = fields.Char(readonly=True)
    dosing_perfomance = fields.Char(readonly=True)

    @api.one
    def _get_lot_moves(self):
        wh = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)])
        input_packop_ids = self.env['stock.pack.operation'].search([
            ('product_id', '=', self.product_id.id),
            ('lot_id', '=', self.lot_id.id),
            ('location_id.usage', '=', 'supplier'),
            ('location_dest_id', '=', wh.wh_input_stock_loc_id.id),
            ('picking_id.picking_type_id', '=', wh.in_type_id.id),
        ], order='date')
        if input_packop_ids:
            self.write({
                'supplier_id': input_packop_ids[0].picking_id.partner_id.id,
                'date_received': input_packop_ids[0].date,
                'supplier_lot': self.lot_id.supplier_lot,
                'qty_received': sum(input_packop_ids.mapped('product_qty'))
            })

        lt_id = self.env['lot.tracking'].create({
            'product_id': self.product_id.id,
            'lot_id': self.lot_id.id,
            'type_of_move': 'io'
        })
        lt_id.get_traceability()
        moves_by_origin = {}
        for m_id in lt_id.lot_move_ids:
            if not m_id.origin:
                key = m_id.date  # Use date as key when there is no origin document
            else:
                key = m_id.origin
            production_id = False
            if key.startswith('MO'):
                production_id = self.env['mrp.production'].search([
                    ('name', '=', m_id.origin)
                ])
            sign = -1 if m_id.type == 'output' else 1
            if not moves_by_origin.has_key(key):
                moves_by_origin[key] = {
                    'production': production_id,
                    'date': production_id.date_planned if production_id else \
                            m_id.date,
                    'location': m_id.location_id.id,
                    'destination': m_id.location_dest_id.id,
                    'qty': m_id.qty * sign
                }
            else:
                moves_by_origin[key]['qty'] += m_id.qty * sign
        lt_id.unlink()

        inventory_adj_move_ids = self.env['stock.move'].search([
            ('product_id', '=', self.product_id.id),
            ('inventory_id', '!=', False),
            ('location_id', 'in', (5, 73)),
            ('location_dest_id', 'in', (5, 73)),
            ('state', '=', 'done'),
            ('origin', 'like', 'MO%')
        ])
        for m_id in inventory_adj_move_ids:
            key = m_id.origin
            production_id = self.env['mrp.production'].search([
                ('name', '=', m_id.origin)
            ])
            sign = -1 if m_id.location_id == 73 else 1
            if not moves_by_origin.has_key(key):
                moves_by_origin[key] = {
                    'production': production_id,
                    'date': production_id.date_planned,
                    'location': m_id.location_id.id,
                    'destination': m_id.location_dest_id.id,
                    'qty': m_id.product_qty * sign
                }
            else:
                moves_by_origin[key]['qty'] += m_id.product_qty * sign

        lot_move_ids = [(5, 0, 0)]
        for key in moves_by_origin:
            production_id = moves_by_origin[key]['production']
            real_consumed_qty = moves_by_origin[key]['qty']

            move_date = False
            theo_manuf_units = 0
            real_manuf_units = 0
            theo_consumed_qty = 0

            if production_id:
                # Manufacturing orders registers and Final revisions registers
                view_ids = production_id.product_id.protocol_ids.\
                    mapped('protocol').\
                    mapped('report_lines.line_id').\
                    mapped('report_reference_ids').\
                    filtered(lambda r: r.report_type_id.id == 2)
                for view_id in view_ids:
                    table_model = self.env[view_id.model_id.model]
                    order_ids = production_id.workcenter_lines
                    section_ids = table_model.x_section_id.search([
                        ('x_wcl_id', 'in', order_ids.ids),
                        ('x_table_ids', '!=', False)
                    ])
                    for section_id in section_ids:
                        manuf_record = section_id.x_table_ids.\
                            sorted(key=lambda r: r.x_create_date)
                        if manuf_record:
                            if (not move_date) or \
                               move_date > manuf_record[0].x_create_date:
                                move_date = manuf_record[0].x_create_date

                bom_qty = sum(production_id.bom_id.bom_line_ids.\
                    filtered(lambda l: l.product_id == self.product_id).\
                    mapped('product_qty'))
                if bom_qty:
                    lt_id = self.env['lot.tracking'].create({
                        'product_id': production_id.product_id.id,
                        'lot_id': production_id.final_lot_id.id,
                        'type_of_move': 'io'
                    })
                    lt_id.get_traceability()
                    real_manuf_units = sum(
                        lt_id.lot_move_ids.
                            filtered(lambda m: m.type == 'input' and
                                               m.location_id.usage == 'production'). \
                            mapped('qty')
                    )
                    lt_id.unlink()
                    theo_manuf_units = abs(real_consumed_qty) / bom_qty
                    theo_consumed_qty = real_manuf_units * bom_qty * \
                                        -1 if real_consumed_qty < 0 else 1
            elif key[:2] == 'SO':
                theo_consumed_qty = real_consumed_qty

            lot_move_ids += [(0, 0, {
                'origin': key if key[:2] in ('PO', 'SO', 'MO') else '',
                'date': move_date if move_date else
                        moves_by_origin[key]['date'],
                'product_id': production_id.product_id.id if production_id else
                              self.product_id.id,
                'lot_id': production_id.final_lot_id.id if production_id else
                          self.lot_id.id,
                'location_id': moves_by_origin[key]['location'],
                'location_dest_id': moves_by_origin[key]['destination'],
                'real_consumed_qty': real_consumed_qty,
                'theoretical_produced_units': theo_manuf_units,
                'real_produced_units': real_manuf_units,
                'theoretical_consumed_qty': theo_consumed_qty,
                'stock_qty': 0
            })]
        self.write({'lot_move_ids': lot_move_ids})

        qty = 0
        input = 0
        output = 0
        dosing = 0
        for lm_id in self.lot_move_ids.sorted(key=lambda m: m.date):
            qty += lm_id.real_consumed_qty
            lm_id.stock_qty = qty
            if lm_id.real_consumed_qty > 0:
                input += lm_id.real_consumed_qty
            else:
                dosing -= lm_id.real_consumed_qty
                output -= lm_id.theoretical_consumed_qty

        self.harnessing = '{:.2%} / in: {:.2f} / out: {:.2f}'.\
            format(output / (input if input else 1), input, output)
        self.dosing_perfomance = '{:.2%} / in: {:.2f} / out: {:.2f}'.\
            format(dosing / (input if input else 1), input, dosing)

    @api.onchange('product_id')
    def clear_all_data(self):
        self.lot_id = False
        self.clear_data()

    @api.onchange('lot_id')
    def clear_data(self):
        self.supplier_id = False
        self.date_received = False
        self.supplier_lot = False
        self.qty_received = False
        self.lot_move_ids = False

    @api.multi
    def get_traceability(self):
        self._get_lot_moves()