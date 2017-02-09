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
from openerp import models, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def write(self, vals):
        orig_values = {}
        attrs = self.fields_get()
        for product in self:
            orig_values[product.id] = {}
            for field in vals:
                field_value = eval('product.' + field)
                field_type = attrs[field]['type']
                if field_type in ['one2many', 'many2one', 'many2many']:
                    orig_values[product.id][field] = u", ".join(
                        [x.display_name for x in field_value]
                    )
                else:
                    orig_values[product.id][field] = field_value

        res = super(ProductProduct, self).write(vals)

        for product in self:
            fields = ''
            for field in vals:
                field_value = eval('product.' + field)
                field_type = attrs[field]['type']
                if field_type == 'binary':
                    new_value = _('(new binary data)') if field_value else False
                elif field_type in ['one2many', 'many2one', 'many2many']:
                    new_value = u", ".join(
                        [x.display_name for x in field_value]
                    )
                else:
                    new_value = field_value

                if field_type == 'binary':
                    orig_value = _('(old binary data)') if \
                        orig_values[product.id][field] else False
                else:
                    orig_value = orig_values[product.id][field]

                orig_value = orig_value if orig_value else _('(no data)')
                new_value = new_value if new_value else _('(no data)')
                fields += u'<br>{0}: {1} >> {2}'.format(
                        _(attrs[field]['string']), orig_value, new_value)

            product.message_post(body=_('Modified fields: ') + fields)

        return res
