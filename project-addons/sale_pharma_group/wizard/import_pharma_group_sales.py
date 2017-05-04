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
import time
import base64
import xlrd
import StringIO
import calendar


class ImportPharmaGroupSales(models.TransientModel):

    _name = "import.pharma.group.sales.wzd"
    _description = "Wizard to import month's pharma groups sales"

    def _get_current_year(self):
        return int(time.strftime("%Y"))

    month = fields.Selection([('01', 'January'), ('02', 'February'),
                              ('03', 'March'), ('04', 'April'), ('05', 'May'),
                              ('06', 'June'), ('07', 'July'), ('08', 'August'),
                              ('09', 'September'), ('10', 'October'),
                              ('11', 'November'), ('12', 'December')],
                             'Month', required=True)
    year = fields.Integer('Year', required=True,
                          default=_get_current_year)
    import_file = fields.Binary('File to import', required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist',
                                   domain=[('type', '=', 'sale')],
                                   required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    category_id = fields.Many2one('res.partner.category', 'Category',
                                  required=True)

    def _get_positions(self, header):
        for pos in range(0, len(header)):
            if header[pos] == u'farmacia':
                p_name_pos = pos
            elif header[pos] == u'dirección':
                p_street_pos = pos
            elif header[pos] == u'CP':
                p_zip_pos = pos
            elif header[pos] == u'población':
                p_location_pos = pos
            elif header[pos] == u'CN':
                cn_pos = pos
            elif header[pos] == u'unidades':
                qty_pos = pos
        return p_name_pos, p_street_pos, p_zip_pos, p_location_pos, cn_pos, qty_pos

    @api.one
    def action_import(self):
        fil = base64.b64decode(self.import_file)
        data = xlrd.open_workbook(file_contents=StringIO.StringIO(fil).read())
        sh = data.sheet_by_index(0)
        product_env = self.env['product.product'].\
            with_context(pricelist=self.pricelist_id.id)
        pharma_env = self.env['pharma.group.sale']
        zip_env = self.env['res.better.zip']
        last_month_day = calendar.monthrange(self.year, int(self.month))[1]
        imp_date = str(self.year) + "-" + self.month + "-" + \
            str(last_month_day)

        header = sh.row_values(0)
        p_name_pos, p_street_pos, p_zip_pos, p_location_pos, cn_pos, qty_pos = self._get_positions(header)
        for line in range(1, sh.nrows):
            row = sh.row_values(line)
            cn_code = row[cn_pos].strip().replace("'", "")
            if '.' not in cn_code:
                cn_code = cn_code[:-1] + '.' + cn_code[-1]
            p_ids = product_env.search([('cn_code', '=', cn_code)])
            if not p_ids:
                raise exceptions.Warning(_('Any product found with CN %s')
                                         % cn_code)
            zip = str(int(row[p_zip_pos])).strip().rjust(5, '0')
            zip_ids = zip_env.search([('name', '=', zip), ('country_id', '=', self.env.ref('base.es').id)])
            if not zip_ids:
                raise exceptions.Warning(_('Zip %s not found') % zip)
            if not zip_ids[0].agent_ids.filtered(
                    lambda r: r.category_id == self.category_id):
                raise exceptions.Warning(_('Zip %s didn\'t have agent set')
                                         % zip)

            pharma_env.create({'pharmacy_name': row[p_name_pos],
                               'pharmacy_street': row[p_street_pos],
                               'pharmacy_zip': zip,
                               'pharmacy_location': row[p_location_pos],
                               'product_cn': row[cn_pos],
                               'product_qty': row[qty_pos],
                               'product_id': p_ids[0].id,
                               'agent_id': zip_ids[0].agent_ids.filtered(
                                lambda r: r.category_id == self.category_id)[0].agent_id.id,
                               'date': imp_date,
                               'price_unit': p_ids[0].price,
                               'price_subtotal': p_ids[0].price * row[qty_pos],
                               'partner_id': self.partner_id.id
                               })
