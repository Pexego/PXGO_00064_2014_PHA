# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _, exceptions


class StockMove(models.Model):
    _inherit = 'stock.move'

    lots_string = fields.Char(compute='_compute_lots_string', string='Lots', store=True, index=True)
    categ_ids = fields.Many2many(related='product_id.categ_ids', readonly=True)
    purchase_amount = fields.Float(related='purchase_line_id.gross_amount',
                                   readonly=True)
    purchase_expected_date = fields.Date(
        related='picking_id.purchase_order.minimum_planned_date',
        readonly=True)
    virtual_conservative = fields.Float(
        related='product_id.virtual_conservative', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda self: self.env.user.company_id)
    product_description = fields.Text(related='product_id.description',
                                      readonly=True)
    kg = fields.Float(compute='_compute_kg', digits=(16, 2))

    @api.one
    @api.constrains('state')
    def compute_detailed_stock(self):
        self.product_id.product_tmpl_id.compute_detailed_stock()

    @api.one
    @api.depends('reserved_quant_ids', 'quant_ids')
    def _compute_lots_string(self):
        quant_ids = self.sudo().with_context(active_test=False).\
                        reserved_quant_ids + \
                    self.sudo().with_context(active_test=False).quant_ids
        lots_string = u", ".join(quant_ids.mapped('lot_id.name'))
        self.lots_string = lots_string

    @api.one
    @api.depends('product_uom_qty', 'product_uom')
    def _compute_kg(self):
        prod_wn = self.product_id.weight_net
        qty = self.product_uom_qty
        uom = self.product_uom
        if uom.category_id == self.env.ref('product.product_uom_categ_kgm'):
            kg = qty / uom.factor
        elif uom.category_id == self.env.ref('product.product_uom_categ_unit'):
            kg = qty * prod_wn / uom.factor
        else:  # Unit of measure not compatible with weight
            kg = 0
        self.kg = kg

    @api.model
    def create(self, vals):
        if 'procurement_id' in vals:
            procure_id = self.env['procurement.order'].\
                browse(vals['procurement_id'])
            if procure_id.sale_line_id and \
                    procure_id.sale_line_id.order_id.location_dest_id:
                vals['location_dest_id'] = \
                    procure_id.sale_line_id.order_id.location_dest_id.id
        return super(StockMove, self).create(vals)


class StockPickingExpeditionsSizes(models.Model):
    _name = 'stock.picking.expedition.sizes'

    package_number = fields.Integer(required=True)
    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        domain="[('expeditions_name', '!=', False)]"
    )
    name = fields.Char(compute='_get_name')
    width = fields.Float('Width (cm)')
    height = fields.Float('Height (cm)')
    depth = fields.Float('Depth (cm)')
    weight = fields.Float('Weight (kg)')
    picking_id = fields.Many2one(comodel_name='stock.picking')

    @api.one
    def _get_name(self):
        self.name = self.product_id.expeditions_name if self.product_id else ''

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.width  = self.product_id.expeditions_width
            self.height = self.product_id.expeditions_height
            self.depth  = self.product_id.expeditions_depth
            self._get_name()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    address_city = fields.Char(related='partner_id.city', readonly=True)
    address_zip = fields.Char(related='partner_id.zip', readonly=True)
    address_country = fields.Char(related='partner_id.country_id.name',
                                  readonly=True)
    picking_type_desc = fields.Char(compute='_compute_picking_type_desc')
    send_invoice_by_email = fields.Boolean(
        related='partner_id.send_invoice_by_email', readonly=True)
    photo_url = fields.Char('Photo(s) URL')
    responsible_uid = fields.Many2one(comodel_name='res.users',
                                      string='Responsible',
                                      compute='_determine_responsible')
    return_reason = fields.Many2one(comodel_name='return.reason')
    return_reason_details = fields.Text()
    expedition_sizes_ids = fields.One2many(
        string='Expedition sizes',
        comodel_name='stock.picking.expedition.sizes',
        inverse_name='picking_id')
    expedition_sizes_loaded = fields.Boolean(compute='_expedition_sizes_loaded')
    expedition_sizes_weight = fields.Float(compute='_expedition_sizes_weight')

    @api.one
    def _expedition_sizes_loaded(self):
        self.expedition_sizes_loaded = True if self.expedition_sizes_ids \
            else False

    @api.one
    def _expedition_sizes_weight(self):
        self.expedition_sizes_weight = \
            sum(self.expedition_sizes_ids.mapped(lambda s: round(s.weight, 2)))

    @api.multi
    def configure_packages_sizes(self):
        for picking_id in self:
            picking_id.expedition_sizes_ids.unlink()
            expedition_sizes_ids = []
            for i in range(1, picking_id.number_of_packages + 1):
                expedition_sizes_ids += [(0, 0, {
                    'package_number': i,
                    'product_id': False,
                    'width': 0,
                    'height': 0,
                    'depth': 0,
                    'weight': 0.0
                })]
            picking_id.write({'expedition_sizes_ids': expedition_sizes_ids})

    @api.multi
    def action_invoice_create(self, journal_id, group=False, type='out_invoice'):
        invoices = super(StockPicking, self).action_invoice_create(journal_id,
                                                                   group, type)
        todo = {}
        for picking in self:
            partner = self.with_context(type=type)._get_partner_to_invoice(picking)
            if group:
                key = partner
            else:
                key = picking.id
            for move in picking.move_lines:
                if move.invoice_state == '2binvoiced' and \
                   move.state != 'cancel' and \
                   move.scrapped: # Add scrapped moves also
                        todo.setdefault(key, [])
                        todo[key].append(move)
        for moves in todo.values():
            invoices += self._invoice_create_line(moves, journal_id, type)

        return invoices

    @api.one
    def _determine_responsible(self):
        if self.picking_type_id == self.env.ref('stock.picking_type_in'):
            if self.purchase_order:
                self.responsible_uid = self.purchase_order.create_uid.id
            elif self.origin:
                po = self.purchase_order.search([('name', '=', self.origin)])
                if po:
                    self.responsible_uid = po.create_uid.id
                else:
                    self.responsible_uid = self.create_uid.id
            else:
                self.responsible_uid = self.create_uid.id
        else:
            self.responsible_uid = self.create_uid.id

    @api.one
    @api.depends('picking_type_id')
    def _compute_picking_type_desc(self):
        types = {'outgoing': ' - (Albarán de salida)',
                 'incoming': ' - (Albarán de entrada)',
                 'internal': ' - (Albarán interno)'}
        self.picking_type_desc = types.get(self.picking_type_id.code, '')

    @api.multi
    def _check_reserved_quantities(self):
        unmatched_quantities_found = False
        for picking in self:
            for move in picking.move_lines:
                if move.product_id.type == 'consu':
                    continue
                unmatched_quantities_found |= move.partially_available
                if not unmatched_quantities_found:
                    sum = 0
                    for quant in move.reserved_quant_ids:
                        sum += quant.qty
                    diff = abs(sum - move.product_qty)
                    unmatched_quantities_found = diff > 0.001

        if unmatched_quantities_found:
            return self.env['custom.views.warning'].show_message(
                _('Stock assignment warning'),
                _('WARNING: There are stock reservations that do not match!')
            )
        return False

    @api.multi
    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        return self._check_reserved_quantities() or res

    @api.multi
    def rereserve_pick(self):
        super(StockPicking, self).rereserve_pick()
        return self._check_reserved_quantities()

    @api.multi
    def confirm_action_cancel(self):
        view = self.env.ref('custom_views.custom_views_picking_cancel_confirm_form')
        return {
            'name': _('Confirm picking cancellation'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }

    @api.multi
    def duplicate(self):
        res = self.copy()

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': res.id,
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
            'nodestroy': True,
            'context': self.env.context
        }

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

            order_id = self.env[model].search([
                ('company_id', '=', self.company_id.id),
                ('name', '=', origin.strip())
            ])

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

    @api.multi
    def write(self, vals):
        date_done = vals.get('date_done')
        if date_done:
            dt = fields.Datetime.context_timestamp(self, fields.Datetime.
                                                   from_string(date_done))
            for picking_id in self:
                picking_id.message_post(subject='Albarán transferido: ' +
                                        dt.strftime('%d/%m/%Y %H:%M:%S'))
        return super(StockPicking, self).write(vals)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    lot_state = fields.Selection(string='Lot state', related='lot_id.state',
                                 readonly=True)
    incoming_picking_id = fields.Many2one('stock.picking', 'Incoming picking',
                                          compute='_incoming_picking_id')

    @api.one
    def _incoming_picking_id(self):
        picking_ids = self.move_ids.mapped('picking_id').\
            filtered(lambda p: p.picking_type_code == 'incoming').\
            sorted(key=lambda p: p.id)
        self.incoming_picking_id = picking_ids[0] if picking_ids else False

    @api.multi
    def unlink(self):
        if self._context.get('nodelete', False):
            raise exceptions.Warning(_('Deletion avoided'),
                                     _('Quants erasing is not allowed'))
        return super(StockQuant, self).unlink()


class StockHistory(models.Model):
    _inherit = 'stock.history'

    categ_ids = fields.Many2many(related='product_id.categ_ids', readonly=True)
    active = fields.Boolean(related='product_id.active', readonly=True)
    line = fields.Many2one(related='product_id.line', readonly=True)
    subline = fields.Many2one(related='product_id.subline', readonly=True)
    purchase_line = fields.Many2one(related='product_id.purchase_line',
                                    readonly=True)
    purchase_subline = fields.Many2one(related='product_id.purchase_subline',
                                       readonly=True)
    sale_ok = fields.Boolean(related='product_id.sale_ok', readonly=True)
    purchase_ok = fields.Boolean(related='product_id.purchase_ok',
                                 readonly=True)
    hr_expense_ok = fields.Boolean(related='product_id.hr_expense_ok',
                                   readonly=True)
    type = fields.Selection(related='product_id.type', readonly=True)


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    default_code = fields.Char(related='product_id.default_code', store=True,
                               readonly=True)
    categ_id = fields.Many2one(related='product_id.categ_id', store=True,
                               readonly=True)
    categ_ids = fields.Many2many(related='product_id.categ_ids', store=True,
                                 readonly=True)
    available_stock = fields.Float(string='Available stock',
                                   compute='_available_stock')
    product_uom_id = fields.Many2one(related='product_id.uom_id', readonly=True)
    input_qty = fields.Float(string='Income qty', compute='_input_qty')
    input_uom = fields.Many2one(string='Income unit of measure',
                                comodel_name='product.uom',
                                compute = '_input_qty')
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda self: self.env.user.company_id)
    kg = fields.Float(compute='_compute_kg', digits=(16, 3))

    @api.one
    def _available_stock(self):
        quantity = 0
        for q in self.quant_ids:
            if q.location_id.usage in ('internal', 'view'):
                quantity += q.qty
        self.available_stock = quantity

    @api.one
    def _input_qty(self):
        quantity = 0
        uom = []
        wh = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)])
        input_location_ids = wh.wh_input_stock_loc_id._get_child_locations()
        for m in self.move_related_ids:
            if m.state == 'done' and (
                    m.location_dest_id in input_location_ids or
                    m.location_id == self.env.ref('stock.location_inventory')):
                quantity += m.product_uom_qty
                if m.product_uom not in uom:
                    uom += m.product_uom
        self.input_qty = quantity
        self.input_uom = uom[0] if len(uom) == 1 else self.product_id.uom_po_id

    @api.one
    def _compute_kg(self):
        prod_wn = self.product_id.weight_net
        qty = self.available_stock
        uom = self.product_uom_id
        if uom.category_id == self.env.ref('product.product_uom_categ_kgm'):
            kg = qty / uom.factor
        elif uom.category_id == self.env.ref('product.product_uom_categ_unit'):
            kg = qty * prod_wn / uom.factor
        else:  # Unit of measure not compatible with weight
            kg = 0
        self.kg = kg


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    notes = fields.Text()


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    product_description = fields.Text(related='product_id.description',
                                      readonly=True)


class StockLocation(models.Model):
    _inherit = 'stock.location'

    dismissed_location = fields.Boolean(default=False)


class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    outgoing_picking = fields.Boolean(
        compute='_outgoing_picking'
    )
    has_lot_certification_and_release = fields.Boolean(
        compute='_has_lot_certification_and_release'
    )
    entry_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        compute='_entry_picking_id'
    )

    @api.multi
    def action_show_lot(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.production.lot',
            'target': 'current',
            'res_id': self.lot_id.id,
        }

    @api.multi
    def _has_lot_certification_and_release(self):
        for po in self:
            if po.outgoing_picking:
                po.has_lot_certification_and_release = False
            else:
                attachment_id = self.env['ir.attachment'].search(
                    [('res_model', '=', po.lot_id._name),
                     ('res_id', '=', po.lot_id.id),
                     ('datas_fname', '=ilike', 'certifica%')])
                po.has_lot_certification_and_release = True if attachment_id \
                    else False

    @api.multi
    def _entry_picking_id(self):
        wh = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)])
        for po in self:
            if po.outgoing_picking:
                po.entry_picking_id = False
            else:
                pack_operation_ids = self.env['stock.pack.operation'].search([
                    ('lot_id', '=', po.lot_id.id),
                    ('location_dest_id', '=', wh.wh_input_stock_loc_id.id),
                    ('picking_id.state', '=', 'done')
                ], order='picking_id')
                po.entry_picking_id = pack_operation_ids[0].picking_id \
                    if pack_operation_ids else False

    @api.multi
    def _outgoing_picking(self):
        for po in self:
            po.outgoing_picking = '\\OUT\\' in po.picking_id.name

    @api.multi
    def action_get_last_certificate(self):
        self.ensure_one()
        attachment_id = self.env['ir.attachment'].search(
            [('res_model', '=', self.lot_id._name),
             ('res_id', '=', self.lot_id.id),
             ('datas_fname', '=ilike', 'certifica%')],
            order='id desc')
        if attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/binary/saveas?model=ir.attachment&field=datas' +
                       '&filename_field=name&id=%s' % (attachment_id[0].id),
                'target': 'self',
            }
        else:
            raise exceptions.Warning('No se generó ningún certificado de '
                                     'liberación de lote...')

    @api.multi
    def action_entry_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'target': 'current',
            'res_id': self.entry_picking_id.id,
        }
