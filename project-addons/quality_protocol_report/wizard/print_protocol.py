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
from openerp import models, fields, api, exceptions, _
from openerp.addons.website.models.website import slug
from urlparse import urljoin


class PrintProtocol(models.TransientModel):

    _name = "print.protocol"

    @api.model
    def _get_type_ids(self):
        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if active_model == u'stock.production.lot':
            production = self.env['mrp.production'].search([('final_lot_id', '=', active_id)])
        else:
            production = self.env[active_model].browse(active_id)
        res = []
        for workcenter in production.workcenter_lines:
            if workcenter.workcenter_id.protocol_type_id.id not in res:
                res.append(workcenter.workcenter_id.protocol_type_id.id)
        return res

    print_url = fields.Char('Print link', readonly=True, compute='_get_print_url')
    protocol_type_id = fields.Many2one('protocol.type', 'Protocol type', required=True)
    type_ids = fields.Many2many('protocol.type', 'protocol_type_wizard_rel_',
                                'wizard_id', 'protocol_id', 'Type', default=_get_type_ids)
    use_continuation = fields.Many2one('mrp.production.workcenter.line',
                                       'Continuation')
    is_continuation = fields.Boolean('Is continuation')

    @api.one
    def _get_print_url(self):
        """Genera la url de impresión,  el controller la espera en este
           formato, pasa como parámetros la producción y el protocolo"""
        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if self.env.context.get('relative_url'):
            base_url = '/'
        else:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if active_model == u'stock.production.lot':
            obj = self.env['mrp.production'].search([('final_lot_id', '=', active_id)])
            if not obj:
                return ""
        else:
            obj = self.env[active_model].browse(active_id)

        use_protocol = False
        wkcenter_line = False
        if self.protocol_type_id.is_continuation:
            wkcenter_line = self.use_continuation
        else:
            for workcenter_line in obj.workcenter_lines:
                if workcenter_line.workcenter_id.protocol_type_id.id == self.protocol_type_id.id:
                    wkcenter_line = workcenter_line
            if not wkcenter_line:
                raise exceptions.Warning(_('Not found'), _('Protocol not found for the route %s.') % obj.routing_id.name)
        protocol_link = obj.product_id.protocol_ids.filtered(lambda r: r.protocol.type_id.id == self.protocol_type_id.id)
        use_protocol = protocol_link.filtered(lambda r: obj.routing_id == r.route and obj.bom_id == r.bom)
        if not use_protocol:
            use_protocol = protocol_link.filtered(lambda r: obj.routing_id == r.route or obj.bom_id == r.bom)
        if not use_protocol:
            use_protocol = protocol_link.filtered(lambda r: not r.route and not r.bom)
        if not use_protocol:
            raise exceptions.Warning(_('Not found'), _('Protocol not found for the product %s.') % obj.product_id.name)
        else:
            use_protocol = use_protocol.protocol
        if not wkcenter_line.realized_ids:
            for line in use_protocol.report_line_ids:
                if line.log_realization:
                    self.env['quality.realization'].create(
                        {
                            'name': line.name,
                            'workcenter_line_id': wkcenter_line.id
                        })

        self.print_url = urljoin(base_url, "protocol/print/%s/%s/%s" % (slug(obj), slug(use_protocol), slug(wkcenter_line)))

    @api.onchange('protocol_type_id')
    def onchange_protocol_type_id(self):
        wkcenter_line_obj = self.env['mrp.production.workcenter.line']
        self.is_continuation = self.protocol_type_id.is_continuation
        if not self.protocol_type_id.is_continuation:
            return {'domain': {'use_continuation': []}}
        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if active_model == u'stock.production.lot':
            production_id = self.env['mrp.production'].search([('final_lot_id', '=', active_id)]).id
        else:
            production_id = active_id
        continuation_work_ids = wkcenter_line_obj.search(
            [('workcenter_id', 'in', [x.id for x in
                                      self.protocol_type_id.workcenter_ids]),
             ('production_id', '=', production_id)])
        return {'domain': {'use_continuation': [('id', 'in', [x.id for x in continuation_work_ids])]}}


    @api.multi
    def print_protocol(self):
        # Abre vista web
        if self.env.context['active_model'] == u'stock.production.lot':
            obj = self.env['mrp.production'].search([('final_lot_id', '=', self.env.context['active_id'])])
            if not obj:
                raise exceptions.Warning(_('Protocol error'), _('The lot not have a production'))
        else:
            obj = self.env[self.env.context['active_model']].browse(self.env.context['active_id'])
        return {
            'type': 'ir.actions.act_url',
            'name': "Print Protocol",
            'target': 'self',
            'url': self.print_url,
        }
