# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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

from openerp import fields, models


class sale(models.Model):

    _inherit = 'sale.order'

    transfer = fields.Boolean('Transfer')
    notified_partner_id = fields.Many2one('res.partner', 'Cooperative')
    settled = fields.Boolean('Settled', readonly=True, default=False)

    settlement_agent_id = fields.Many2one('settlement.agent', 'Settlement')

    def action_quotation_send(self, cr, uid, ids, context=None):
        '''
        Se sobreescribe para utilizar un template diferente para los pedidos
        transfer
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        order = self.browse(cr, uid, ids[0], context)
        try:
            if order.transfer:
                template_id = ir_model_data.get_object_reference(cr, uid,
                                                                 'sale_transfer',
                                                                 'email_template_sale_transfer')[1]
            else:
                template_id = ir_model_data.get_object_reference(cr, uid, 'sale',
                                                                 'email_template_edi_sale')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail',
                                                                 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'sale.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class sale_order_line(models.Model):

    _inherit = 'sale.order.line'

    def get_applied_commission(self, line):
        if not line.product_id.commission_exent:
            # si la linea no tiene comissiones arrastro los del pedido a la
            # linea de factura
            commissions = []
            if not line.line_agent_ids:
                for so_comm in line.order_id.sale_agent_ids:
                    commissions.append(so_comm)
            else:
                for l_comm in line.line_agent_ids:
                    commissions.append(l_comm)
        return commissions
