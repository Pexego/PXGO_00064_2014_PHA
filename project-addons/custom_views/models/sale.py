# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
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

from openerp import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(SaleOrder, self).onchange_partner_id(cr, uid, ids, part, context)
        intermediary = context.get('intermediary', False)

        # Dynamic filters for invoice and shipping combos
        if part and intermediary:
            res['domain'] = {
                'partner_invoice_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False),
                    '|', ('parent_id', '=', part), ('id', '=', part)
                ],
                'partner_shipping_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False)
                ]
            }
        elif part and not intermediary:
            res['domain'] = {
                'partner_invoice_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False),
                    '|', ('parent_id', '=', part), ('id', '=', part)
                ],
                'partner_shipping_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False),
                    '|', ('parent_id', '=', part), ('id', '=', part)
                ]
            }
        else:
            res['domain'] = {
                'partner_invoice_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False)
                ],
                'partner_shipping_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False)
                ]
            }

        # Recover default partner picking policy
        if part:
            partner_id = self.pool.get('res.partner').browse(cr, uid, part)
            if partner_id.picking_policy:
                res['value']['picking_policy'] = partner_id.picking_policy
            else:
                ir_values = self.pool.get('ir.values')
                picking_policy = ir_values.get_default(cr, uid, 'sale.order',
                                                       'picking_policy')
                res['value']['picking_policy'] = picking_policy

        return res
