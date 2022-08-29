# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import datetime


class StockLotMove(models.TransientModel):
    _name = 'stock.lot.move'
    _order = 'date'

    lot_tracking_id = fields.Many2one(comodel_name='lot.tracking')
    lot_id = fields.Many2one(comodel_name='stock.production.lot')
    move_id = fields.Many2one(comodel_name='stock.move')
    date = fields.Datetime(string='Date')
    product_uom = fields.Many2one(string='Unit of measure',
                                  comodel_name='product.uom')
    location_id = fields.Many2one(string='Source Location',
                                  comodel_name='stock.location')
    location_dest_id = fields.Many2one(string='Destination location',
                                       comodel_name='stock.location')
    partner_id = fields.Many2one(string='Partner', comodel_name='res.partner')
    picking_id = fields.Many2one(string='Reference',
                                 comodel_name='stock.picking')
    origin = fields.Char()
    final_product_id = fields.Many2one(comodel_name='product.product')
    final_lot_id = fields.Many2one(comodel_name='stock.production.lot')
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Ready to Transfer'),
        ('done', 'Transferred'),
    ])
    qty = fields.Float(string='Quantity')
    type = fields.Char(compute='_check_type')
    stock_inventory_note = fields.Text()
    temperature_date_from = fields.Datetime()
    temperature_date_to = fields.Datetime()
    temperature_url = fields.Char(compute='_generate_temperature_url')

    @api.one
    def _generate_temperature_url(self):
        temp_date_from = self.temperature_date_from
        temp_date_to = self.temperature_date_to

        def unix_time_millis(dt):
            epoch = datetime.datetime.utcfromtimestamp(0)
            return int((dt - epoch).total_seconds() * 1000)

        self.temperature_url = self.env['ir.config_parameter']. \
            get_param('lot_tracking.temperature_url'). \
            format(
                unix_time_millis(fields.Datetime.from_string(temp_date_from)),
                unix_time_millis(fields.Datetime.from_string(temp_date_to))
            )

    @api.one
    def _check_type(self):
        internal_usage = ('internal', 'view')
        external_usage = ('customer', 'inventory', 'supplier', 'production',
                          'procurement', 'transit')
        if (self.location_id.usage in internal_usage) and\
           (self.location_dest_id.usage in external_usage):
            self.type = 'output'
        elif (self.location_id.usage in external_usage) and\
             (self.location_dest_id.usage in internal_usage):
            self.type = 'input'
        else:
            self.type = 'internal'

    @api.multi
    def action_show_origin(self):
        self.ensure_one()
        origin = self.origin
        if origin and origin.strip():
            if origin[0:2] == 'PO':
                model = 'purchase.order'
            elif origin[0:2] == 'SO':
                model = 'sale.order'
            elif origin[0:2] == 'MO':
                model = 'mrp.production'
            else:
                model = 'stock.picking'

            origin_id = self.env[model].search([('name', '=', origin.strip())])

            if origin_id:
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': model,
                    'res_id': origin_id.id,
                    'target': 'current',
                    'nodestroy': True,
                    'context': self.env.context
                }


class LotTracking(models.Model):
    _name = 'lot.tracking'
    _rec_name = 'product_id'
    _order = 'write_date desc'

    product_id = fields.Many2one(comodel_name='product.product',
                                 domain="[('sequence_id', '!=', False), '|', "
                                        "('active', '=', True), "
                                        "('active', '=', False)]")
    lot_id = fields.Many2one(comodel_name='stock.production.lot',
                             domain="[('product_id', '=', product_id)]")
    type_of_move = fields.Selection(string='Type of moves',
        selection=[('all', 'All movements'),('io', 'Inputs & Outputs')],
        default='io', required=True)

    lot_move_ids = fields.One2many(comodel_name='stock.lot.move',
                                   inverse_name='lot_tracking_id',
                                   readonly=True)
    total = fields.Float(string='Total', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company',
                                 related='product_id.company_id',
                                 readonly=True)

    @api.one
    def _get_lot_moves(self):
        if self.type_of_move == 'all':
            quant_ids = self.lot_id.quant_ids
            move_ids = quant_ids.mapped('move_ids')
        else:
            quant_ids = self.env['stock.quant']
            move_ids = self.env['stock.move']
            internal_usage = ('internal', 'view')
            external_usage = ('customer', 'inventory', 'supplier', 'production',
                              'procurement', 'transit')
            for quant_id in self.lot_id.quant_ids:
                for move_id in quant_id.move_ids:
                    if (move_id.location_id.usage in internal_usage and \
                        move_id.location_dest_id.usage in external_usage) \
                       or \
                       (move_id.location_id.usage in external_usage and \
                        move_id.location_dest_id.usage in internal_usage):
                        quant_ids |= quant_id
                        move_ids |= move_id

        self.lot_move_ids.unlink()
        temperature_date_from = quant_ids.\
            filtered(lambda q: q.id == min(quant_ids.mapped('id'))).create_date
        for quant_id in quant_ids:
            for move_id in quant_id.move_ids:
                if move_id in move_ids:
                    lm_id = self.lot_move_ids.filtered(lambda m:
                        m.date == move_id.date and \
                        m.location_id == move_id.location_id and \
                        m.location_dest_id == move_id.location_dest_id
                    )
                    if lm_id:
                        lm_id.qty += quant_id.qty
                        if lm_id.temperature_date_to < quant_id.write_date:
                            lm_id.temperature_date_to = quant_id.write_date
                    else:
                        origin = move_id.picking_id.origin \
                            if move_id.picking_id.origin else move_id.origin
                        final_product_id = False
                        final_lot_id = False
                        stock_inventory_note = False
                        if origin and origin[0:2] == 'MO':
                            production_id = self.env['mrp.production'].search(
                                [('name', '=', origin)])
                            if production_id:
                                final_product_id = production_id.product_id.id
                                final_lot_id = production_id.final_lot_id.id
                        else:
                            stock_inventory_id = self.\
                                env['stock.inventory'].search([
                                    ('move_ids', 'in', [move_id.id])
                                ])
                            if stock_inventory_id:
                               stock_inventory_note = stock_inventory_id.notes

                        self.write({'lot_move_ids': [(0, 0, {
                            'lot_id': self.lot_id.id,
                            'move_id': move_id.id,
                            'date': move_id.date,
                            'product_uom': move_id.product_uom.id,
                            'location_id': move_id.location_id.id,
                            'location_dest_id': move_id.location_dest_id.id,
                            'partner_id': move_id.picking_id.partner_id.id,
                            'picking_id': move_id.picking_id.id,
                            'origin': origin,
                            'final_product_id': final_product_id,
                            'final_lot_id': final_lot_id,
                            'state': move_id.state,
                            'qty': quant_id.qty,
                            'stock_inventory_note': stock_inventory_note,
                            'temperature_date_from': temperature_date_from,
                            'temperature_date_to': quant_id.write_date,
                        })]})

        total = 0
        for move_id in self.lot_move_ids:
            if move_id.type == 'input':
                total += move_id.qty
            elif move_id.type == 'output':
                total -= move_id.qty
        self.total = total

    @api.onchange('product_id')
    def clear_lot(self):
        self.lot_id = False
        self.clear_lot_moves()

    @api.onchange('lot_id', 'type_of_move')
    def clear_lot_moves(self):
        self.lot_move_ids = False
        self.total = 0

    @api.multi
    def get_traceability(self):
        self._get_lot_moves()


class StockLotMoveFromOrigin(models.TransientModel):
    _name = 'stock.lot.move.from.origin'
    _inherit = 'stock.lot.move'

    lot_tracking_id = fields.Many2one(comodel_name='lot.tracking.from.origin')
    product_id = fields.Many2one(comodel_name='product.product')

    @api.one
    def _check_type(self):
        internal_usage = ['internal', 'production']
        external_usage = ['customer', 'inventory', 'supplier', 'view',
                          'procurement', 'transit']
        if (self.location_id.usage in internal_usage) and\
           (self.location_dest_id.usage in external_usage):
            self.type = 'output'
        elif (self.location_id.usage in external_usage) and\
             (self.location_dest_id.usage in internal_usage):
            self.type = 'input'
        else:
            self.type = 'internal'


class LotTrackingFromOrigin(models.Model):
    _name = 'lot.tracking.from.origin'
    _inherit = 'lot.tracking'

    lot_move_ids = fields.One2many(comodel_name='stock.lot.move.from.origin',
                                   inverse_name='lot_tracking_id',
                                   readonly=True)

    def _get_lot_movements(self, lot_id):
        quant_ids = lot_id.quant_ids
        move_ids = quant_ids.mapped('move_ids')
        temperature_date_from = quant_ids.\
            filtered(lambda q: q.id == min(quant_ids.mapped('id'))).create_date
        for quant_id in quant_ids:
            for move_id in quant_id.move_ids:
                if move_id in move_ids:
                    lm_id = self.lot_move_ids.filtered(lambda m:
                        m.date == move_id.date and \
                        m.location_id == move_id.location_id and \
                        m.location_dest_id == move_id.location_dest_id
                    )
                    if lm_id:
                        lm_id.qty += quant_id.qty
                        if lm_id.temperature_date_to < quant_id.write_date:
                            lm_id.temperature_date_to = quant_id.write_date
                    else:
                        origin = move_id.picking_id.origin \
                            if move_id.picking_id.origin else move_id.origin
                        final_product_id = False
                        final_lot_id = False
                        if origin and origin[0:2] == 'MO':
                            production_id = self.env['mrp.production'].search(
                                [('name', '=', origin)])
                            if production_id:
                                final_product_id = production_id.product_id.id
                                final_lot_id = production_id.final_lot_id.id

                        self.write({'lot_move_ids': [(0, 0, {
                            'lot_id': lot_id.id,
                            'move_id': move_id.id,
                            'date': move_id.date,
                            'product_id': move_id.product_id.id,
                            'product_uom': move_id.product_uom.id,
                            'location_id': move_id.location_id.id,
                            'location_dest_id': move_id.location_dest_id.id,
                            'partner_id': move_id.picking_id.partner_id.id,
                            'picking_id': move_id.picking_id.id,
                            'origin': move_id.picking_id.origin if \
                                move_id.picking_id.origin else move_id.origin,
                            'final_product_id': final_product_id,
                            'final_lot_id': final_lot_id,
                            'state': move_id.state,
                            'qty': quant_id.qty,
                            'temperature_date_from': temperature_date_from,
                            'temperature_date_to': quant_id.write_date,
                        })]})

    @api.one
    def _get_lot_moves(self):
        self.lot_move_ids.unlink()
        self._get_lot_movements(self.lot_id)

        # Get movements of related productions lots
        lot_ids = {self}
        prod_obj = self.env['mrp.production']
        move_ids = self.lot_move_ids.filtered(lambda m: m.id == 0)
        while self.lot_move_ids - move_ids:
            move_id = (self.lot_move_ids - move_ids)[0]
            move_ids += move_id
            if move_id.origin and move_id.origin[0:2] == 'MO':
                prod_id = prod_obj.search([('name', '=', move_id.origin.strip())])
                final_lot_id = prod_id.final_lot_id
                if prod_id and final_lot_id and final_lot_id not in lot_ids:
                    lot_ids.add(final_lot_id)
                    self._get_lot_movements(final_lot_id)

        # If the user only wants inputs and outputs, remove internal moves
        if self.type_of_move == 'io':
            self.lot_move_ids.filtered(lambda m: m.type == 'internal').unlink()


class StockLotMoveFromOriginEcoKg(models.TransientModel):
    _name = 'stock.lot.move.from.origin.eco.kg'
    _inherit = 'stock.lot.move.from.origin'

    lot_tracking_id = fields.Many2one(comodel_name='lot.tracking.from.origin.eco.kg')
    kg = fields.Float(precision=(16,3), compute='_calculate_kg')

    @api.one
    def _calculate_kg(self):
        prod_wn = self.product_id.weight_net
        qty = self.qty
        uom = self.product_uom
        if uom.category_id == self.env.ref('product.product_uom_categ_kgm'):
            qty = qty / uom.factor
        elif uom.category_id == self.env.ref(
                'product.product_uom_categ_unit'):
            qty = qty / uom.factor
        else:  # Unit of measure not compatible with weight
            qty = 0

        if self.product_id == self.lot_tracking_id.product_id:
            self.kg = qty
            return

        lot_product_id = self.lot_tracking_id.product_id
        lot_product_tmpl_id = lot_product_id.product_tmpl_id

        def _get_raw_material_weight(product_id):
            raw_material_id = product_id.weight_net_eco_ids.\
                filtered(lambda p: p.component_id == lot_product_tmpl_id)
            if raw_material_id:
                kg = product_id.weight_net * raw_material_id.percent / 100.0
                return kg
            else:
                bom_ids = product_id.bom_ids.sorted(key=lambda b: b.sequence)
                if bom_ids:
                    bom_line_id = bom_ids[0].bom_line_ids.\
                        filtered(lambda l: l.product_id == lot_product_id)
                    if bom_line_id:
                        return bom_line_id.product_qty
                    else:
                        total = 0.0
                        for bl in bom_ids[0].bom_line_ids:
                            total += bl.product_qty * \
                                     (_get_raw_material_weight(bl.product_id) or 0)
                        return total
                elif product_id.pack_line_ids:
                    total = 0.0
                    for pl in product_id.pack_line_ids:
                        total += pl.quantity * \
                                 (_get_raw_material_weight(pl.product_id) or 0)
                    return total
                else:
                    return 0.0

        self.kg = qty * _get_raw_material_weight(self.product_id)


class LotTrackingFromOriginEcoKg(models.Model):
    _name = 'lot.tracking.from.origin.eco.kg'
    _inherit = 'lot.tracking.from.origin'

    lot_move_ids = fields.One2many(comodel_name='stock.lot.move.from.origin.eco.kg',
                                   inverse_name='lot_tracking_id',
                                   readonly=True)


class StockLotMoveFromDestination(models.TransientModel):
    _name = 'stock.lot.move.from.destination'
    _inherit = 'stock.lot.move'

    lot_tracking_id = fields.Many2one(comodel_name='lot.tracking.from.destination')
    product_id = fields.Many2one(comodel_name='product.product')

    @api.one
    def _check_type(self):
        internal_usage = ['internal', 'production']
        external_usage = ['customer', 'inventory', 'supplier', 'view',
                          'procurement', 'transit']
        if (self.location_id.usage in internal_usage) and\
           (self.location_dest_id.usage in external_usage):
            self.type = 'output'
        elif (self.location_id.usage in external_usage) and\
             (self.location_dest_id.usage in internal_usage):
            self.type = 'input'
        else:
            self.type = 'internal'


class LotTrackingFromDestination(models.Model):
    _name = 'lot.tracking.from.destination'
    _inherit = 'lot.tracking'

    lot_move_ids = fields.One2many(comodel_name='stock.lot.move.from.destination',
                                   inverse_name='lot_tracking_id',
                                   readonly=True)

    def _get_lot_movements(self, lot_id):
        productions = {}
        consumption_lot_ids = []
        if self.type_of_move == 'all':
            quant_ids = lot_id.quant_ids
            move_ids = quant_ids.mapped('move_ids')
        else:
            quant_ids = self.env['stock.quant']
            move_ids = self.env['stock.move']
            internal_usage = ('internal', 'view')
            external_usage = ('customer', 'inventory', 'supplier', 'production',
                              'procurement', 'transit')
            for quant_id in lot_id.quant_ids:
                for move_id in quant_id.move_ids:
                    if (move_id.location_id.usage in internal_usage and \
                        move_id.location_dest_id.usage in external_usage) \
                       or \
                       (move_id.location_id.usage in external_usage and \
                        move_id.location_dest_id.usage in internal_usage):
                        quant_ids |= quant_id
                        move_ids |= move_id

        for quant_id in quant_ids:
            for move_id in quant_id.move_ids:
                if move_id in move_ids:
                    lm_id = self.lot_move_ids.filtered(lambda m:
                        m.product_id == move_id.product_id and \
                        m.date == move_id.date and \
                        m.location_id == move_id.location_id and \
                        m.location_dest_id == move_id.location_dest_id
                    )
                    if lm_id:
                        lm_id.qty += quant_id.qty
                        if lm_id.temperature_date_from > quant_id.create_date:
                            lm_id.temperature_date_from = quant_id.create_date
                        if lm_id.temperature_date_to < quant_id.write_date:
                            lm_id.temperature_date_to = quant_id.write_date
                    else:
                        origin = move_id.picking_id.origin \
                            if move_id.picking_id.origin else move_id.origin
                        final_product_id = False
                        final_lot_id = False
                        stock_inventory_note = False
                        if origin and origin[0:2] == 'MO':
                            if origin not in productions:
                                production_id = self.env['mrp.production'].search(
                                    [('name', '=', origin)])
                                if production_id:
                                    productions[origin] = {
                                        'product_id': production_id.product_id.id,
                                        'lot_id': production_id.final_lot_id.id
                                    }
                                    final_product_id = \
                                        productions[origin]['product_id']
                                    final_lot_id = productions[origin]['lot_id']
                                    lot_ids = self.\
                                        _production_consumed_lots(production_id)
                                    for lot_id in lot_ids:
                                        if lot_id not in consumption_lot_ids:
                                            consumption_lot_ids += lot_id
                            else:
                                final_product_id = \
                                    productions[origin]['product_id']
                                final_lot_id = productions[origin]['lot_id']
                        else:
                            stock_inventory_id = self.\
                                env['stock.inventory'].search([
                                    ('move_ids', 'in', quant_id.move_ids.ids)
                                ])
                            if stock_inventory_id:
                                stock_inventory_note = stock_inventory_id.notes

                        temperature_date_from = quant_id.create_date
                        temperature_date_to = quant_id.write_date

                        self.write({'lot_move_ids': [(0, 0, {
                            'lot_id': lot_id.id,
                            'move_id': move_id.id,
                            'date': move_id.date,
                            'product_uom': move_id.product_uom.id,
                            'location_id': move_id.location_id.id,
                            'location_dest_id': move_id.location_dest_id.id,
                            'partner_id': move_id.picking_id.partner_id.id,
                            'picking_id': move_id.picking_id.id,
                            'origin': origin,
                            'final_product_id': final_product_id,
                            'final_lot_id': final_lot_id,
                            'state': move_id.state,
                            'qty': quant_id.qty,
                            'stock_inventory_note': stock_inventory_note,
                            'temperature_date_from': temperature_date_from,
                            'temperature_date_to': temperature_date_to,
                        })]})
        return consumption_lot_ids

    @api.one
    def _get_lot_moves(self):
        self.lot_move_ids.unlink()
        processed_lot_ids = []
        consumption_lot_ids = [self.lot_id]
        while consumption_lot_ids:
            lot_id = consumption_lot_ids.pop()
            processed_lot_ids += lot_id
            for new_lot_id in self._get_lot_movements(lot_id):
                if new_lot_id not in processed_lot_ids and \
                    new_lot_id not in consumption_lot_ids:
                    consumption_lot_ids += new_lot_id


    def _production_consumed_lots(self, production_id):
        consumptions = []
        # Gathering pickings
        for po in production_id.hoard_ids.sudo().\
                filtered(lambda p: p.state == 'done').\
                mapped('pack_operation_ids'):
            idx = -1
            for i, obj in enumerate(consumptions):
                if obj['product_id'] == po.product_id.id and \
                        obj['lot_id'] == po.lot_id:
                    idx = i
            if idx > -1:
                consumptions[idx]['quantity'] += po.product_qty
            else:
                consumptions.append({
                    'product_id': po.product_id.id,
                    'lot_id': po.lot_id,
                    'quantity': po.product_qty,
                 })

        # Return moves
        for m in production_id.move_lines2.sudo().filtered(
                lambda r: r.location_id.usage == 'internal' and
                          r.location_dest_id.usage == 'internal'):
            idx = -1
            for i, obj in enumerate(consumptions):
                if obj['product_id'] == m.product_id.id and \
                        obj['lot_id'] == (m.lot_ids[0] if m.lot_ids
                                          else False):
                    idx = i
            if idx > -1:
                consumptions[idx]['quantity'] -= m.product_qty
            else:
                consumptions.append({
                    'product_id': m.product_id.id,
                    'lot_id': m.lot_ids[0] if m.lot_ids else False,
                    'quantity': -m.product_qty,
                })

        # Return pickings
        for po in production_id.manual_return_pickings.sudo().\
                filtered(lambda p: p.state == 'done').\
                mapped('pack_operation_ids'):
            idx = -1
            for i, obj in enumerate(consumptions):
                if obj['product_id'] == po.product_id.id and \
                        obj['lot_id'] == po.lot_id:
                    idx = i
            sign = -1 if po.location_dest_id.usage == 'internal' else 1
            if idx > -1:
                consumptions[idx]['quantity'] += po.product_qty * sign
            else:
                consumptions.append({
                    'product_id': po.product_id.id,
                    'lot_id': po.lot_id,
                    'quantity': po.product_qty * sign,
                })

        lot_ids = []
        for c in consumptions:
            if c['quantity'] != 0 and c['lot_id']:
                lot_ids += [c['lot_id']]
        return lot_ids


class StockLotMoveBySeal(models.TransientModel):
    _name = 'stock.lot.move.by.seal'
    _inherit = 'stock.lot.move'

    lot_tracking_id = fields.Many2one(comodel_name='lot.tracking.by.seal')
    product_id = fields.Many2one(comodel_name='product.product')


class LotTrackingBySeal(models.Model):
    _name = 'lot.tracking.by.seal'
    _inherit = 'lot.tracking'

    lot_move_ids = fields.One2many(comodel_name='stock.lot.move.by.seal',
                                   inverse_name='lot_tracking_id',
                                   readonly=True)

    date_from = fields.Date(required=True)
    date_to = fields.Date(default=fields.Date.today(), required=True)
    category_id = fields.Many2one(comodel_name='product.category')

    @api.one
    def _get_lot_moves(self):
        query = """
            select
                sq.id
            from stock_quant sq
            join stock_quant_move_rel sqmr on sqmr.quant_id = sq.id
            join stock_move sm on sm.id = sqmr.move_id
            join product_product pp on pp.id = sm.product_id
            join product_categ_rel pcr on pcr.product_id = pp.product_tmpl_id
            where pcr.categ_id = {category}
              and sm.date between '{date_from}'::date and '{date_to}'::date        
        """
        self.env.cr.execute(query.format(
            category=self.category_id.id,
            date_from=self.date_from,
            date_to=self.date_to
        ))
        res = self.env.cr.fetchall()
        target_quant_ids = self.env['stock.quant'].browse(
            map(lambda x: x[0], res)
        )
        if self.type_of_move == 'all':
            quant_ids = target_quant_ids
            move_ids = target_quant_ids.mapped('move_ids')
        else:
            quant_ids = self.env['stock.quant']
            move_ids = self.env['stock.move']
            internal_usage = ('internal', 'view')
            external_usage = ('customer', 'inventory', 'supplier', 'production',
                              'procurement', 'transit')
            for quant_id in target_quant_ids:
                for move_id in quant_id.move_ids:
                    if (move_id.location_id.usage in internal_usage and \
                        move_id.location_dest_id.usage in external_usage) \
                       or \
                       (move_id.location_id.usage in external_usage and \
                        move_id.location_dest_id.usage in internal_usage):
                        quant_ids |= quant_id
                        move_ids |= move_id

        self.lot_move_ids.unlink()
        temperature_date_from = quant_ids.\
            filtered(lambda q: q.id == min(quant_ids.mapped('id'))).create_date
        for quant_id in quant_ids:
            for move_id in quant_id.move_ids:
                if move_id in move_ids:
                    lm_id = self.lot_move_ids.filtered(lambda m:
                        m.date == move_id.date and \
                        m.location_id == move_id.location_id and \
                        m.location_dest_id == move_id.location_dest_id
                    )
                    if lm_id:
                        lm_id.qty += quant_id.qty
                        if lm_id.temperature_date_to < quant_id.write_date:
                            lm_id.temperature_date_to = quant_id.write_date
                    else:
                        origin = move_id.picking_id.origin \
                            if move_id.picking_id.origin else move_id.origin
                        final_product_id = False
                        final_lot_id = False
                        stock_inventory_note = False
                        if origin and origin[0:2] == 'MO':
                            production_id = self.env['mrp.production'].search(
                                [('name', '=', origin)])
                            if production_id:
                                final_product_id = production_id.product_id.id
                                final_lot_id = production_id.final_lot_id.id
                        else:
                            stock_inventory_id = self.\
                                env['stock.inventory'].search([
                                    ('move_ids', 'in', [move_id.id])
                                ])
                            if stock_inventory_id:
                               stock_inventory_note = stock_inventory_id.notes

                        self.write({'lot_move_ids': [(0, 0, {
                            'lot_id': quant_id.lot_id.id,
                            'product_id': move_id.product_id.id,
                            'move_id': move_id.id,
                            'date': move_id.date,
                            'product_uom': move_id.product_uom.id,
                            'location_id': move_id.location_id.id,
                            'location_dest_id': move_id.location_dest_id.id,
                            'partner_id': move_id.picking_id.partner_id.id,
                            'picking_id': move_id.picking_id.id,
                            'origin': origin,
                            'final_product_id': final_product_id,
                            'final_lot_id': final_lot_id,
                            'state': move_id.state,
                            'qty': quant_id.qty,
                            'stock_inventory_note': stock_inventory_note,
                            'temperature_date_from': temperature_date_from,
                            'temperature_date_to': quant_id.write_date,
                        })]})

        total = 0
        for move_id in self.lot_move_ids:
            if move_id.type == 'input':
                total += move_id.qty
            elif move_id.type == 'output':
                total -= move_id.qty
        self.total = total
