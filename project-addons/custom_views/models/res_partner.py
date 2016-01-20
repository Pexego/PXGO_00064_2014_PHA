# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus All Rights Reserved
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

from openerp import models, fields, api
from openerp.osv.expression import get_unaccent_wrapper


class ResPartner(models.Model):
    _inherit = 'res.partner'

    picking_policy = fields.Selection(
            [
                ('direct', 'Deliver each product when available'),
                ('one', 'Deliver all products at once')
            ],
            'Shipping Policy',
            states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
            help="""Pick 'Deliver each product when available' if you allow partial delivery.""")

    @api.multi
    def name_get(self):
        key = 'concatenate_name_comercial'

        # If key is defined and form is in create mode
        if key in self._context and self._context.get(key):
            res = []
            for rec in self:
                name = rec.name + \
                       (' (' + rec.comercial + ')' if rec.comercial else '')
                res.append((rec.id, name))
            return res
        else:
            return super(ResPartner, self).name_get()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):

            self.check_access_rights('read')
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            query = """SELECT id
                         FROM res_partner
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent}
                           OR {comercial} {operator} {percent})
                     ORDER BY {display_name}
                    """.format(where=where_str, operator=operator,
                               email=unaccent('email'),
                               display_name=unaccent('display_name'),
                               comercial=unaccent('comercial'),
                               percent=unaccent('%s'))

            where_clause_params += [search_name, search_name, search_name]
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            ids = map(lambda x: x[0], self.env.cr.fetchall())

            if ids:
                return self.browse(ids).name_get()
            else:
                return []
        return super(ResPartner,self).name_search(name, args, operator=operator, limit=limit)
