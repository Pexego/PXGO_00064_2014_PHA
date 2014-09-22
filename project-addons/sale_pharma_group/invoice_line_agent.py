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

from openerp import models, fields, exceptions, _


class invoice_agent(models.Model):

    _inherit = 'invoice.line.agent'


    def calculate_commission(self, cr, uid, ids):
        commission_obj = self.pool.get('commission.bussines.line')
        for line_agent in self.browse(cr, uid, ids):
            analytic = line_agent.invoice_line_id.account_analytic_id
            commission_applied = commission_obj.search(cr, uid, [('bussiness_line_id', '=', analytic.id), ('commission_id', '=', line_agent.commission_id.id)])
            if not commission_applied:
                commission_applied = commission_obj.search(cr, uid, [('bussiness_line_id', '=', False), ('commission_id', '=', line_agent.commission_id.id)])
            if not commission_applied:
                raise exceptions.except_orm(_('Commission Error'), _('not found the appropiate commission.'))
            commission = commission_obj.browse(cr, uid, commission_applied[0])
            if commission.type == 'fijo' and \
                    commission.fix_qty:
                quantity = line_agent.invoice_line_id.price_subtotal * \
                    (commission.fix_qty / 100.0)
                self.write(cr, uid, line_agent.id, {'quantity': quantity})
