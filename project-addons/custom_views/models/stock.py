# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _, exceptions


class StockMove(models.Model):
    _inherit = 'stock.move'

    computed_lots_string = fields.Char(compute='_compute_lots_string')
    lots_string = fields.Char(string='Lots', readonly=True, store=True, index=True)
    categ_ids = fields.Many2many(related='product_id.categ_ids', readonly=True)
    purchase_amount = fields.Float(related='purchase_line_id.gross_amount',
                                   readonly=True)
    purchase_expected_date = fields.Date(
        related='picking_id.purchase_order.minimum_planned_date',
        readonly=True)
    virtual_conservative = fields.Float(
        related='product_id.virtual_conservative', readonly=True)

    @api.one
    @api.constrains('state')
    def compute_detailed_stock(self):
        self.product_id.product_tmpl_id.compute_detailed_stock()

    @api.one
    def _compute_lots_string(self):
        lots_string = u", ".join(
            (self.reserved_quant_ids + self.quant_ids).mapped('lot_id.name')
        )
        self.write({
            'computed_lots_string': lots_string,
            'lots_string':lots_string
        })


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
                unmatched_quantities_found = unmatched_quantities_found or \
                    move.partially_available
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


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    lot_state = fields.Selection(string='Lot state', related='lot_id.state',
                                 readonly=True)

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
    input_qty = fields.Float(string='Income qty', compute='_input_qty')
    input_uom = fields.Many2one(string='Income unit of measure',
                                comodel_name='product.uom',
                                compute = '_input_qty')

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

    @api.multi
    def action_show_lot(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.production.lot',
            'target': 'current',
            'res_id': self.lot_id.id,
        }
