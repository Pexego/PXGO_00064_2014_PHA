# -*- coding: utf-8 -*-
# © 2014 Pexego
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from datetime import date
import openerp.addons.decimal_precision as dp


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    state = fields.Selection(
        (('draft', 'New'), ('in_rev', 'Revision(Q)'), ('revised', 'Revised'),
         ('approved', 'Approved'), ('rejected', 'Rejected')),
        'State', default='draft')

    state_depends = fields.Many2many('stock.production.lot',
                                     'final_material_lot_rel', 'final_lot_id',
                                     'material_lot_id', 'Dependencies')
    dependent_lots = fields.Many2many('stock.production.lot',
                                      'final_material_lot_rel',
                                      'material_lot_id', 'final_lot_id',
                                      'Dependencies')
    is_revised = fields.Boolean('Is material lots revised',
                                compute='_is_revised')
    rejected_from = fields.Char('Rejected from')
    acceptance_date = fields.Date('Acceptance date')
    partner_id = fields.Many2one('res.partner', 'Supplier')
    is_returned = fields.Boolean('is Returned')
    is_returnable = fields.Boolean('Is returnable',
                                   compute='_get_is_returnable')
    active = fields.Boolean('Active', default=True)
    entry_quarantine = fields.Date('Entry quarantine')
    detail_ids = fields.One2many(comodel_name='stock.lot.detail',
                                 inverse_name='lot_id')

    @api.one
    @api.depends('quant_ids')
    def _get_is_returnable(self):
        quants = self.env['stock.quant'].search(
            [('lot_id', '=', self.id),
             ('location_id', '=',
              self.env.ref('lot_states.stock_location_rejected').id)])
        self.is_returnable = bool(quants)

    @api.one
    def _is_revised(self):
        self.is_revised = True
        for lot in self.state_depends:
            if lot.state == 'in_rev':
                self.is_revised = False

    @api.multi
    def move_lot(self, dest_id, ignore_location_ids, pick_type='internal',
                 from_location=False):
        """
            Se recorren todos los quants, si tienen un movimiento asignado se
            cambia la localizacion de destino, si no se crea un movimiento a
            la localizacion de destino.
        """
        picking_ids = []
        for lot in self:
            if not from_location:
                locations = sorted(set([x.location_id.id for x in lot.quant_ids
                                        if x.location_id.id not in
                                        ignore_location_ids]))
            else:
                locations = [from_location]
            search_domain = [('lot_id', '=', lot.id), ('location_id', 'in',
                                                       locations)]
            not_assigned_quant_ids = []
            for quant in self.env['stock.quant'].search(search_domain):
                if quant.reservation_id:
                    if quant.reservation_id.state != 'done' and \
                            quant.reservation_id.picking_id.pack_operation_ids:
                        quant.reservation_id.picking_id.pack_operation_ids.unlink()
                    quant.reservation_id.cancel_chain()
                    move = quant.reservation_id
                    dest_picking = self.env['stock.picking'].search(
                        [('group_id', '=', move.group_id.id),
                         ('location_id', '=', move.location_id.id),
                         ('location_dest_id', '=', dest_id)])
                    if dest_picking:
                        if len(move.picking_id.move_lines) > 1:
                            move.picking_id = dest_picking
                        picking_ids.append(dest_picking)
                    else:
                        if len(move.picking_id.move_lines) > 1:
                            new_picking = move.picking_id.copy({'move_lines':
                                                               False})
                            move.picking_id = new_picking
                            picking_ids.append(new_picking)
                    move.write({'location_dest_id': dest_id})

                else:
                    not_assigned_quant_ids.append(quant.id)

            """
            search_domain.append(('id', 'in', not_assigned_quant_ids))
            quants = self.env['stock.quant'].read_group(
                search_domain, ['location_id', 'qty'], ['location_id'])

            for quant in quants:
                location = self.env['stock.location'].browse(
                    quant['location_id'][0])
                wh = self.env['stock.location'].get_warehouse(location)
                type_search_dict = [('code', '=', pick_type)]
                if wh:
                    type_search_dict.append(('warehouse_id', '=', wh))
                picking_type = self.env['stock.picking.type'].search(
                    type_search_dict)
                picking_vals = {
                    'picking_type_id': picking_type.id,
                    'partner_id': self.env.context.get('partner_id', ''),
                    'date': date.today(),
                    'origin': lot.name
                }
                picking_id = self.env['stock.picking'].create(picking_vals)

                move_dict = {
                    'name': lot.product_id.name or '',
                    'product_id': lot.product_id.id,
                    'product_uom': lot.product_id.uom_id.id,
                    'product_uos': lot.product_id.uom_id.id,
                    'restrict_lot_id': lot.id,
                    'product_uom_qty': quant['qty'],
                    'date': date.today(),
                    'date_expected': datetime.now(),
                    'location_id': location.id,
                    'location_dest_id': dest_id,
                    'move_dest_id': False,
                    'state': 'draft',
                    'partner_id': self.env.context.get('partner_id', ''),
                    'company_id': self.env.user.company_id.id,
                    'picking_type_id': picking_type.id,
                    'procurement_id': False,
                    'origin': lot.name,
                    'invoice_state': 'none',
                    'picking_id': picking_id.id
                }
                self.env['stock.move'].create(move_dict).action_confirm()
            """
        return picking_ids

    @api.multi
    def action_in_rev(self):
        self.write({'state': 'in_rev', 'entry_quarantine': date.today()})

    @api.multi
    def action_approve(self):
        """
            Se impide aprobar un lote cuando aun tiene dependencias sin
            aprobar.
        """
        for lot in self:
            for depends_lot in lot.state_depends:
                if depends_lot.state != 'approved':
                    raise exceptions.Warning(
                        _('material lot error'),
                        _('Material lot %s not approved') % depends_lot.name)
        self.write({'state': 'approved', 'acceptance_date': date.today()})

    @api.multi
    def button_approved(self):
        self.ensure_one()
        if self.product_id.analytic_certificate and not self.analysis_passed:
            raise exceptions.Warning(
                _('Analysis error'),
                _('the consignment has not passed all analysis'))
        else:
            wizard_id = self.env['stock.lot.detail.wizard']. \
                create({'lot_id': self.id})
            view = self.env.ref('lot_states.stock_lot_details_form')
            return {
                'name': _('Lot details'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.lot.detail.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wizard_id.id,
            }

    @api.multi
    def button_lot_details(self):
        return self.button_approved()

    @api.multi
    def act_approved_without_new_moves(self):
        """
            Se impide aprobar un lote cuando aun tiene dependencias sin
            aprobar. Innecesario si no se llama a move_lot desde action_approve
        """
        for lot in self:
            for depends_lot in lot.state_depends:
                if depends_lot.state != 'approved':
                    raise exceptions.Warning(
                        _('material lot error'),
                        _('Material lot %s not approved') % depends_lot.name)
        self.write({'state': 'approved', 'acceptance_date': date.today()})

    @api.multi
    def action_reject(self):
        for lot in self:
            lot.rejected_from = lot.state
            if lot.dependent_lots:
                lot.dependent_lots.signal_workflow('act_rejected')

        rejected_loc_id = self.env.ref('lot_states.stock_location_rejected')
        picking_ids = self.move_lot(rejected_loc_id.id,
                      [self.env.ref('stock.location_production').id])

        self.write({'state': 'rejected', 'acceptance_date': date.today()})

#        for picking in picking_ids:
#            try:
#                if picking.state in ('draft', 'waiting'):
#                    picking.action_confirm()
#                if picking.state not in ('assigned'):
#                    picking.action_assign()
#                picking.do_transfer()
#            except Exception, e:
#                raise e
#                pass

    @api.multi
    def button_approved_to_draft(self):
        self.write({'state': 'draft'})
        self.delete_workflow()
        self.create_workflow()
        return True

    @api.multi
    def button_return_from_rejected(self):
        for lot in self:
            signal = ''
            loc_name = ''
            dest_location = False
            possible_to_location = self.env['stock.location']
            if lot.rejected_from == 'draft':
                loc_name = 'wh_input_stock_loc_id'
                lot.write({'state': 'draft'})
                signal = 'rejected_draft'
            else:
                loc_name = 'wh_qc_stock_loc_id'
                signal = 'rejected_rev'
            for wh in self.env['stock.warehouse'].search([]):
                possible_to_location += self.env['stock.location'].search(
                    [('id', 'child_of', wh[loc_name].id)])
            for quant in lot.quant_ids:
                for move in quant.history_ids:
                    if move.location_dest_id in possible_to_location:
                        dest_location = move.location_dest_id.id
            if dest_location:
                lot.move_lot(dest_location,
                             [self.env.ref('stock.location_production').id])
                lot.signal_workflow(signal)

    @api.multi
    def return_to_supplier(self):
        """
            Se crea un movimiento para toda la parte del lote rechazada hacia
            proveedores.
        """
        context = dict(self.env.context)
        context['partner_id'] = self.partner_id.id
        self.with_context(context).move_lot(
            self.env.ref('stock.stock_location_suppliers').id,
            [self.env.ref('stock.location_production').id], 'outgoing',
            self.env.ref('lot_states.stock_location_rejected').id)
        self.is_returned = True

    @api.one
    def compute_details_from_moves(self):
        wh = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)])
        approved_packop_ids = self.env['stock.pack.operation'].search([
            ('lot_id', '=', self.id),
            ('location_id', 'child_of', wh.wh_qc_stock_loc_id.id),
            ('location_dest_id.usage', '=', 'internal'),
            ('location_dest_id', 'child_of', wh.lot_stock_id.id),
        ])
        rejected_packop_ids = self.env['stock.pack.operation'].search([
            ('lot_id', '=', self.id),
            ('location_id', 'child_of', wh.wh_qc_stock_loc_id.id),
            ('location_dest_id.usage', '=', 'internal'),
            '!',
            ('location_dest_id', 'child_of', wh.lot_stock_id.id),
        ])
        detail_ids = []
        for po in approved_packop_ids + rejected_packop_ids:
            new_detail = True
            for d in detail_ids:
                # Packops of the same picking have identical datetime
                if d[2]['date'] == po.date:
                    new_detail = False
                    d[2]['quantity'] += po.product_qty
            if new_detail:
                state = 'approved' if po in approved_packop_ids else 'rejected'
                if state == 'approved' and self.production_id and \
                        self.production_id.create_date > self.create_date:
                    state = 'reprocessed'
                detail_ids += [(0, 0, {
                    'date': po.date,
                    'state': state,
                    'quantity': po.product_qty
                })]
        # Write back all collected data
        # (5, 0, 0) to clear all previous existing details
        self.write({'detail_ids': [(5, 0, 0)] + detail_ids})


class LotDetail(models.Model):
    _name = 'stock.lot.detail'
    _order = 'date'

    lot_id = fields.Many2one(comodel_name='stock.production.lot')
    date = fields.Date(required=True)
    state = fields.Selection([('approved', 'Approved'),
                              ('rejected', 'Rejected'),
                              ('reprocessed', 'Reprocessed'),
                              ('approved_for_reanalysis', 'Approved for reanalysis'),
                              ('rejected_for_reanalysis', 'Rejected for reanalysis')],
                             required=True)
    quantity = fields.Float(digits=dp.get_precision('Product Unit of Measure'))