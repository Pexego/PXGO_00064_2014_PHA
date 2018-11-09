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
from datetime import date
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, _, exceptions, api, tools
from openerp.addons.product import _common


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    goods_request_date = fields.Date('Request date')
    goods_return_date = fields.Date('Return date')
    picking_notes = fields.Text('Picking notes')
    workcenter_lines = fields.One2many(readonly=False)
    date_end_planned = fields.Datetime()
    time_planned = fields.Float()
    final_qty = fields.Float('Final quantity', copy=False)

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

    @api.multi
    def create_continuation(self):
        protocol_type = self.env['protocol.type'].search([('is_continuation',
                                                           '=', True)])
        if not protocol_type:
            raise exceptions.Warning(_('Protocol error'),
                                     _('continuation protocol type not found'))
        assert len(protocol_type.workcenter_ids) == 1
        workcenter_line_dict = {
            'name': protocol_type.name + ' ' + date.today().strftime('%d-%m-%Y') + ' - ' + self.product_id.name,
            'production_id': self.id,
            'workcenter_id': protocol_type.workcenter_ids[0].id,
            'date_planned': date.today(),
            'continuation': True
        }
        self.env['mrp.production.workcenter.line'].create(workcenter_line_dict)


class MrpBom(models.Model):

    _inherit = 'mrp.bom'

    def _bom_explode(self, cr, uid, bom, product, factor, properties=None,
                     level=0, routing_id=False, previous_products=None,
                     master_bom=None, context=None):
        uom_obj = self.pool.get("product.uom")
        routing_obj = self.pool.get('mrp.routing')
        master_bom = master_bom or bom
        result, result2 = super(MrpBom, self)._bom_explode(
            cr, uid, bom, product, factor, properties, level, routing_id,
            previous_products, master_bom, context)
        for line in result:
            for bom_line_id in bom.bom_line_ids:
                if bom_line_id.product_id.id == line['product_id']:
                    line['workcenter_id'] = bom_line_id.workcenter_id.id,
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

    continuation = fields.Boolean('Is continuation')
    realized_ids = fields.One2many('quality.realization', 'workcenter_line_id',
                                   'Realization')


class MrpWorkcenter(models.Model):

    _inherit = 'mrp.workcenter'

    protocol_type_id = fields.Many2one('protocol.type', 'Associated protocol')
    bom_line_ids = fields.One2many('mrp.bom.line', 'workcenter_id',
                                   'Bom lines')


class MrpBomLine(models.Model):

    _inherit = 'mrp.bom.line'

    workcenter_id = fields.Many2one('mrp.workcenter', 'Workcenter')
