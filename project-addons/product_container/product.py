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

from openerp import models, fields


class product_template(models.Model):

    _inherit = 'product.template'

    base_form_id = fields.Many2one('product.form', 'Base form', required=True)

    container_id = fields.Many2one('product.container', 'Container', required=True)


class product_form(models.Model):

    _name = 'product.form'

    name = fields.Char('Name', size=64)


class product_container(models.Model):

    _name = 'product.container'

    name = fields.Char('Name', size=64)
