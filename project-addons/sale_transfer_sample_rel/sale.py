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

from openerp import fields, models, api


class sale_order(models.Model):

    _inherit = 'sale.order'

    #este campo no se muestra en el formulario de ventas,
    # es usado para filtrar en el informe de ventas y para agrupar en el search
    sale_type = fields.Selection(selection=[('normal', 'Normal'),
                                            ('sample', 'Sample'),
                                            ('transfer', 'Transfer'),
                                            ('replacement', 'Replacement'),
                                            ('intermediary', 'Intermediary')],
                                 string="Type", compute='_get_type',
                                 store=True)

    @api.one
    @api.depends('transfer', 'sample', 'replacement', 'intermediary')
    def _get_type(self):
        if self.transfer:
            self.sale_type = 'transfer'
        elif self.sample:
            self.sale_type = 'sample'
        elif self.replacement:
            self.sale_type = 'replacement'
        elif self.intermediary:
            self.sale_type = 'intermediary'
        else:
            self.sale_type = 'normal'


class sale_order_line(models.Model):
    """
        TODO: mover a otro modulo?
    """
    _inherit = 'sale.order.line'

    virtual_available = fields.Float('Virtual Available',
                                     related='product_id.virtual_available',
                                     digits=(16, 2))
