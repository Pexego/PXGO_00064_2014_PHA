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

from openerp import models, api
from datetime import date


class res_partner(models.Model):

    _inherit = 'res.partner'

    @api.one
    def write(self, vals):
        _today = date.today()
        pricelist_history_obj = self.env['product.pricelist.partner.history']
        pricelist_pur = vals.get('property_product_pricelist_purchase', False)
        pricelist_sale = vals.get('property_product_pricelist', False)
        if pricelist_pur:
            vals_history = {'date': _today, 'pricelist_id':
                            self.property_product_pricelist_purchase.id,
                            'partner_id': self.id}
            vals_history['type'] = 'purchase'
            pricelist_history_obj.create(vals_history)
        if pricelist_sale:
            vals_history = {'date': _today, 'pricelist_id':
                            self.property_product_pricelist.id,
                            'partner_id': self.id}
            vals_history['type'] = 'sale'
            pricelist_history_obj.create(vals_history)
        return super(res_partner, self).write(vals)

    @api.multi
    def view_pricelist_history(self):
        act = self.env.ref('pricelist_history.action_pricelist_history')
        result = act.read()[0]
        result['domain'] = "[('partner_id','='," + str(self.id) + ")]"
        return result
