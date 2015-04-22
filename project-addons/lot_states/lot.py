# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, exceptions, _
from datetime import date, datetime


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
    acceptance_date = fields.Date('Acceptance date')
    partner_id = fields.Many2one('res.partner', 'Supplier')
    is_returned = fields.Boolean('is Returned')
    is_returnable = fields.Boolean('Is returnable',
                                   compute='_get_is_returnable')
    active = fields.Boolean('Active', default=True)
    entry_quarantine = fields.Date('Entry quarantine')

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
                    else:
                        if len(move.picking_id.move_lines) > 1:
                            new_picking = move.picking_id.copy({'move_lines':
                                                               False})
                            move.picking_id = new_picking
                    move.write({'location_dest_id': dest_id})

                    '''orig_picking = quant.reservation_id.picking_id
                    new_picking = quant.reservation_id.picking_id.pick_aux
                    if len(quant.reservation_id.picking_id.move_lines) > 1:
                        if not new_picking:
                            new_picking = orig_picking.copy({'move_lines':
                                                             False})
                            orig_picking.pick_aux = new_picking.id
                        if new_picking:
                            quant.reservation_id.picking_id = new_picking.id
                        if len(orig_picking.move_lines) == 0:
                            orig_picking.action_cancel()
                    # se cambia el destino y se buscan movimientos encadenados
                    # para cancelar.
                    if quant.reservation_id.location_dest_id.id != dest_id:
                        quant.reservation_id.location_dest_id = dest_id
                    quant.reservation_id.cancel_chain()'''
                else:
                    not_assigned_quant_ids.append(quant.id)
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

    @api.multi
    def action_in_rev(self):
        self.write({'state': 'in_rev', 'entry_quarantine': date.today()})

    @api.multi
    def action_approve(self):
        """
            Se impide aprobar un lote cuando aun tiene dependencias sin
            aprobar. En caso de venir de una producción se crea un movimiento
            de Q a stock
        """
        for lot in self:
            for depends_lot in lot.state_depends:
                if depends_lot.state != 'approved':
                    raise exceptions.Warning(
                        _('material lot error'),
                        _('Material lot %s not approved') % depends_lot.name)
        self.move_lot(self.env.ref('stock.stock_location_stock').id,
                      [self.env.ref('stock.location_production').id,
                       self.env.ref('lot_states.stock_location_rejected').id])
        self.write({'state': 'approved', 'acceptance_date': date.today()})

    @api.multi
    def act_approved_without_new_moves(self):
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
    def action_reject(self):
        for lot in self:
            if lot.dependent_lots:
                lot.dependent_lots.signal_workflow('act_rejected')
        self.move_lot(self.env.ref('lot_states.stock_location_rejected').id,
                      [self.env.ref('stock.location_production').id])
        self.write({'state': 'rejected'})

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
