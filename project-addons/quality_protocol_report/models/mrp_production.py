# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, _, exceptions, api, tools
from openerp.addons.product import _common


class MrpProductProduce(models.TransientModel):

    _inherit = 'mrp.product.produce'

    _defaults = {
        'mode': lambda *x: 'consume',
    }

    @api.multi
    def do_produce(self):
        production_id = self.env.context.get('active_id', False)
        production = self.env['mrp.production'].browse(production_id)
        docs_no_submited = []
        for wkcenter_line in production.workcenter_lines:
            if not wkcenter_line.doc_submited:
                if wkcenter_line.workcenter_id.name not in docs_no_submited:
                    docs_no_submited.append(wkcenter_line.workcenter_id.name)
        if docs_no_submited:
            raise exceptions.Warning(_('Document error'), _('Documents not submited: \n %s') % (','.join(docs_no_submited)))
        res = super(MrpProductProduce, self.with_context(no_return_operations=True)).do_produce()
        originals = self.env['stock.move']
        production = self.env['mrp.production'].browse(self.env.context.get('active_id', False))
        for move in production.move_lines:
            operations = move.split_from and move.split_from.return_operation_ids or move.return_operation_ids
            for op in operations:
                if op.qty_scrapped > 0:
                    scrap_location_id = self.env['stock.location'].search(
                            [('scrap_location', '=', True)])
                    if not scrap_location_id:
                        raise exceptions.Warning(_('Location not found'), _('Scrap location not found.'))
                    default_val = {
                            'product_uom_qty': op.qty_scrapped,
                            'served_qty': 0,
                            'returned_qty': 0,
                            'qty_scrapped': 0,
                            'restrict_lot_id': op.lot_id.id,
                            'scrapped': True,
                            'location_dest_id': scrap_location_id[0].id,
                    }
                    move.do_unreserve()
                    move.product_uom_qty -= op.qty_scrapped
                    move.with_context(no_return_operations=True).action_assign()
                    new_move = move.copy(default_val)
                    new_move.action_confirm()
                    new_move.with_context(no_return_operations=True).action_assign()
                    new_move.action_done()
            dest_location = move.raw_material_production_id.location_src_id.id
            if move.original_move:
                if move.original_move.state != 'done':
                    dest_location =  move.original_move.location_id.id
                    move.original_move.do_unreserve()
                    move.original_move.product_uom_qty += move.returned_qty
                    originals += move.original_move
                else:
                    dest_location =  move.original_move.location_dest_id.id
            move.location_dest_id = dest_location
            if len(operations) == 1:
                move.restrict_lot_id = operations[0].lot_id.id
            elif len(operations) > 1:
                move.restrict_lot_id = operations[0].lot_id.id
                move.do_unreserve()
                move.product_uom_qty = operations[0].returned_qty
                for op in operations:
                    if op.id == operations[0]:
                        continue
                    default_val = {
                            'product_uom_qty': op.returned_qty,
                            'served_qty': 0,
                            'returned_qty': 0,
                            'qty_scrapped': 0,
                            'restrict_lot_id': op.lot_id.id,
                            'location_dest_id': dest_location,
                    }
                    new_move = move.copy(default_val)
                    new_move.action_confirm()
                    new_move.with_context(no_return_operations=True).action_assign()
                    new_move.action_done()
                move.with_context(no_return_operations=True).action_assign()
            move.action_done()


        originals.action_assign()
        return res


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    goods_request_date = fields.Date('Request date')
    goods_return_date = fields.Date('Return date')
    picking_notes = fields.Text('Picking notes')
    hoard_ids = fields.One2many('stock.picking', string='hoards', compute='_get_hoard_picking')
    hoard_len = fields.Integer('hoard len', compute = '_get_hoard_len')
    workcenter_lines = fields.One2many(readonly=False)

    @api.one
    @api.depends('hoard_ids')
    def _get_hoard_len(self):
        self.hoard_len = len(self.hoard_ids)

    @api.one
    @api.depends('move_lines.move_orig_ids', 'move_lines2.move_orig_ids')
    def _get_hoard_picking(self):
        pickings = self.env['stock.picking']
        pickings += self.mapped('move_lines.move_orig_ids.picking_id').sorted()
        pickings += self.mapped('move_lines2.move_orig_ids.picking_id').sorted()
        self.hoard_ids = pickings

    def _create_previous_move(self, cr, uid, move_id, product,
                              source_location_id, dest_location_id,
                              context=None):
        if not context:
            context = {}
        proc_obj = self.pool.get('procurement.group')
        move = super(MrpProduction, self)._create_previous_move(
            cr, uid, move_id, product, source_location_id, dest_location_id,
            context)
        prod_name = context.get('production', False)
        move_dict = {
            'workcenter_id': context.get('workcenter_id', False)
        }
        if prod_name:
            procurement = proc_obj.search(cr, uid, [('name', '=', prod_name)],
                                          context=context)
            if not procurement:
                procurement = proc_obj.create(cr, uid, {'name': prod_name},
                                              context)
            else:
                procurement = procurement[0]
            move_dict['group_id'] = procurement
        self.pool.get('stock.move').write(cr, uid, move, move_dict,
                                          context=context)
        return move

    @api.multi
    def get_hoard(self):
        action = self.env.ref('stock.action_picking_tree')
        if not action:
            return
        action = action.read()[0]
        res = self.env.ref('stock.view_picking_form')
        action['views'] = [(res.id, 'form')]
        action['res_id'] = self.hoard_ids and self.hoard_ids[0].id or False
        action['context'] = False
        return action

    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels the production order and related stock moves.
        @return: True
        """
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        for production in self.browse(cr, uid, ids, context=context):
            if production.move_created_ids:
                move_obj.action_cancel(cr, uid, [x.id for x in production.move_created_ids])
            moves = move_obj.search(cr, uid, [('move_dest_id', 'in', [x.id for x in production.move_lines])], context=context)
            if moves:
                move_obj.action_cancel(cr, uid, moves, context=context)
            move_obj.action_cancel(cr, uid, [x.id for x in production.move_lines])
        self.write(cr, uid, ids, {'state': 'cancel'})
        # Put related procurements in exception
        proc_obj = self.pool.get("procurement.order")
        procs = proc_obj.search(cr, uid, [('production_id', 'in', ids)], context=context)
        if procs:
            proc_obj.write(cr, uid, procs, {'state': 'exception'}, context=context)
        return True

    @api.model
    def _make_consume_line_from_data(self, production, product, uom_id,
                                     qty, uos_id, uos_qty):
        my_context = dict(self.env.context)
        my_context['production'] = production.name
        return super(MrpProduction, self.with_context(
            my_context))._make_consume_line_from_data(production, product,
                                                      uom_id, qty, uos_id,
                                                      uos_qty)

    def _make_production_consume_line(self, cr, uid, line, context=None):
        context = dict(context)
        context['workcenter_id'] = line.workcenter_id.id
        move_id = super(MrpProduction, self)._make_production_consume_line(
            cr, uid, line, context)
        self.pool.get('stock.move').write(cr, uid, move_id,
                                          {'workcenter_id':
                                              line.workcenter_id.id}, context)
        return move_id


class MrpBom(models.Model):

    _inherit = 'mrp.bom'

    def _bom_explode(self, cr, uid, bom, product, factor, properties=None,
                     level=0, routing_id=False, previous_products=None,
                     master_bom=None, context=None):
        """
        Finds Products and Work Centers for related BoM for manufacturing
        order.
        @param bom: BoM of particular product template.
        @param product: Select a particular variant of the BoM.
            If False use BoM without variants.
        @param factor: Factor represents the quantity, but in UoM of the BoM,
            taking into account the numbers produced by the BoM
        @param properties: A List of properties Ids.
        @param level: Depth level to find BoM lines starts from 10.
        @param previous_products: List of product previously use by bom
            explore to avoid recursion
        @param master_bom: When recursion, used to display the name of
            the master bom
        @return: result: List of dictionaries containing product details.
                 result2: List of dictionaries containing Work Center details.
        """
        uom_obj = self.pool.get("product.uom")
        routing_obj = self.pool.get('mrp.routing')
        master_bom = master_bom or bom
        super(MrpBom, self)._bom_explode(cr, uid, bom, product, factor,
                                         properties, level, routing_id,
                                         previous_products, master_bom,
                                         context)

        def _factor(factor, product_efficiency, product_rounding):
            factor = factor / (product_efficiency or 1.0)
            factor = _common.ceiling(factor, product_rounding)
            if factor < product_rounding:
                factor = product_rounding
            return factor

        factor = _factor(factor, bom.product_efficiency, bom.product_rounding)

        result = []
        result2 = []

        routing = (routing_id and routing_obj.browse(cr, uid, routing_id)) or \
            bom.routing_id or False
        if routing:
            for wc_use in routing.workcenter_lines:
                wc = wc_use.workcenter_id
                d, m = divmod(factor, wc_use.workcenter_id.capacity_per_cycle)
                mult = (d + (m and 1.0 or 0.0))
                cycle = mult * wc_use.cycle_nbr
                result2.append({
                    'name': tools.ustr(wc_use.name) + ' - ' +
                    tools.ustr(bom.product_tmpl_id.name_get()[0][1]),
                    'workcenter_id': wc.id,
                    'sequence': level + (wc_use.sequence or 0),
                    'cycle': cycle,
                    'hour':
                    float(wc_use.hour_nbr * mult + ((wc.time_start or 0.0) +
                          (wc.time_stop or 0.0) + cycle *
                          (wc.time_cycle or 0.0)) *
                          (wc.time_efficiency or 1.0)),
                })

        for bom_line_id in bom.bom_line_ids:
            if bom_line_id.date_start and bom_line_id.date_start > \
                    time.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or \
                    bom_line_id.date_stop and bom_line_id.date_stop < \
                    time.strftime(DEFAULT_SERVER_DATETIME_FORMAT):
                    continue
            # all bom_line_id variant values must be in the product
            if bom_line_id.attribute_value_ids:
                if not product or \
                        (set(map(int, bom_line_id.attribute_value_ids or [])) -
                            set(map(int, product.attribute_value_ids))):
                    continue

            if previous_products and \
                    bom_line_id.product_id.product_tmpl_id.id in \
                    previous_products:
                raise exceptions.Warning(
                    _('Invalid Action!'),
                    _('BoM "%s" contains a BoM line with a product\
                       recursion: "%s".') %
                    (master_bom.name,
                     bom_line_id.product_id.name_get()[0][1]))

            quantity = _factor(bom_line_id.product_qty *
                               factor, bom_line_id.product_efficiency,
                               bom_line_id.product_rounding)
            bom_id = self._bom_find(cr, uid,
                                    product_id=bom_line_id.product_id.id,
                                    properties=properties, context=context)

            # If BoM should not behave like PhantoM, just add the product,
            # otherwise explode further
            if bom_line_id.type != "phantom" and \
                    (not bom_id or self.browse(cr, uid, bom_id,
                     context=context).type != "phantom"):
                result.append({
                    'name': bom_line_id.product_id.name,
                    'product_id': bom_line_id.product_id.id,
                    'product_qty': quantity,
                    'product_uom': bom_line_id.product_uom.id,
                    'product_uos_qty':
                        bom_line_id.product_uos and
                        _factor(bom_line_id.product_uos_qty * factor,
                                bom_line_id.product_efficiency,
                                bom_line_id.product_rounding) or False,
                    'product_uos':
                        bom_line_id.product_uos and
                        bom_line_id.product_uos.id or False,
                    'workcenter_id': bom_line_id.workcenter_id.id,
                })
            elif bom_id:
                all_prod = [bom.product_tmpl_id.id] + (previous_products or [])
                bom2 = self.browse(cr, uid, bom_id, context=context)
                # We need to convert to units/UoM of chosen BoM
                factor2 = uom_obj._compute_qty(cr, uid,
                                               bom_line_id.product_uom.id,
                                               quantity, bom2.product_uom.id)
                quantity2 = factor2 / bom2.product_qty
                res = self._bom_explode(
                    cr, uid, bom2, bom_line_id.product_id, quantity2,
                    properties=properties, level=level + 10,
                    previous_products=all_prod, master_bom=master_bom,
                    context=context)
                result = result + res[0]
                result2 = result2 + res[1]
            else:
                raise exceptions.Warning(
                    _('Invalid Action!'),
                    _('BoM "%s" contains a phantom BoM line but the product \
                      "%s" does not have any BoM defined.') %
                    (master_bom.name,
                     bom_line_id.product_id.name_get()[0][1]))
        return result, result2


class MrpProductionProductLine(models.Model):

    _inherit = 'mrp.production.product.line'

    workcenter_id = fields.Many2one('mrp.workcenter', 'Workcenter')


class QualityRealization(models.Model):

    _name = 'quality.realization'

    name = fields.Char('Name', size=64)
    realized = fields.Char('Realized by', size=64)
    realization_date = fields.Datetime('Date')
    workcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                         'Workcenter line')


class MrpProductionWorkcenterLine(models.Model):

    _inherit = 'mrp.production.workcenter.line'

    adjustsments_ids = fields.One2many('mrp.production.adjustments',
                                       'production_id', 'Adjustments')
    control_ids = fields.One2many('mrp.production.control',
                                  'Workcenter_line_id', 'Controls')
    realized_ids = fields.One2many('quality.realization', 'workcenter_line_id',
                                   'Realization')
    on_time_machine = fields.Datetime('On time machine')
    wender_temp_ids = fields.One2many('mrp.wender.temp', 'workcenter_line_id',
                                      'Wender temps')
    mrp_speed = fields.Float('Mrp speed')
    adjustement_lever = fields.Float('adjustment lever')
    fallen_scale = fields.Float('Fallen scale')
    slow_funnel = fields.Float('slow funnel')
    fast_funnel = fields.Float('fast funnel')
    printed_configured_by = fields.Char('Configured printer by', size=64)
    confirmed_printer = fields.Char('Confirmed printer', size=64)
    printed_lot = fields.Char('Printed lot', size=64)
    printed_date = fields.Datetime('Printed date')
    print_comprobations = fields.One2many('mrp.print.comprobations',
                                          'wkcenter_line_id',
                                          'Print comprobations')
    doc_submited = fields.Boolean('Document submited')
    mrp_start_date = fields.Datetime('Start production')
    final_count = fields.Integer('Final counter')
    continue_next_day = fields.Boolean('Continue production next day')
    fab_issue = fields.Boolean('Production issue')
    issue_ref = fields.Char('Issue ref', size=64)
    total_produced = fields.Float('Total produced')
    observations = fields.Text('Observations')
    wrap_comprobations = fields.One2many('mrp.wrap.comprobations',
                                         'wkcenter_line_id',
                                         'Print comprobations')
    print_comprobations_sec = fields.One2many('mrp.print.comprobations.sec',
                                              'wkcenter_line_id',
                                              'Print comprobations')

    coffin_works = fields.One2many('mrp.coffin.works', 'wkcenter_line_id',
                                   'Coffin works')
    qty_produced = fields.One2many('mrp.qty.produced', 'wkcenter_line_id',
                                   'Qty produced')
    lot_tag_ok = fields.Boolean('Validated lot number of tags')
    acond_issue = fields.Boolean('issue')
    acond_issue_ref = fields.Char('Issue ref', size=64)
    accond_total_produced = fields.Float('Total produced')
    accond_theorical_produced = fields.Float('theorical produced')
    prod_ratio = fields.Float('production ratio')
    acond_observations = fields.Text('Observations')


class mrpQtyProduced(models.Model):

    _name = 'mrp.qty.produced'

    date = fields.Date('Date')
    coffins = fields.Integer('Coffins')
    boxes = fields.Integer('Boxes')
    case = fields.Integer('Case')
    initials = fields.Char('Initials')
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')


class MrpWrapComprobations(models.Model):

    _name = 'mrp.wrap.comprobations'

    date = fields.Datetime('Date')
    correct = fields.Boolean('Print correct')
    quality_sample = fields.Char('Quality sample', size=64)
    initials = fields.Char('Initials', size=12)
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')
    type = fields.Selection(
        (('wrap', 'Wrap'), ('box', 'Box')),
        'Type')

    @api.model
    def create(self, vals):
        type = self.env.context.get('type', False)
        if 'type' not in vals.keys() and type:
            vals['type'] = type
        return super(MrpWrapComprobations, self).create(vals)


class MrpPrintComprobationsCoffin(models.Model):

    _name = 'mrp.coffin.works'

    init_date = fields.Datetime('Init date')
    end_date = fields.Datetime('End date')
    initials = fields.Char('Initials', size=12)
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')


class MrpPrintComprobations(models.Model):

    _name = 'mrp.print.comprobations'

    date = fields.Datetime('Date')
    correct = fields.Boolean('Print correct')
    initials = fields.Char('Initials', size=12)
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')


class MrpPrintComprobationsSec(models.Model):

    _name = 'mrp.print.comprobations.sec'

    date = fields.Date('Date')
    lot_correct = fields.Boolean('Lot correct')
    date_correct = fields.Boolean('Date correct')
    initials = fields.Char('Initials', size=12)
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')


class MrpWenderTemp(models.Model):

    _name = 'mrp.wender.temp'

    sequence = fields.Integer('Wender nº')
    temperature = fields.Float('Temperature')
    workcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                         'Workcenter line')


class MrpWorkcenter(models.Model):

    _inherit = 'mrp.workcenter'

    protocol_type_id = fields.Many2one('protocol.type', 'Associated protocol')
    bom_line_ids = fields.One2many('mrp.bom.line', 'workcenter_id',
                                   'Bom lines')


class MrpBomLine(models.Model):

    _inherit = 'mrp.bom.line'

    workcenter_id = fields.Many2one('mrp.workcenter', 'Workcenter')
