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

        for line in range(1, sh.nrows):
            row = sh.row_values(line)
            p_ids = product_env.search([('cn_code', '=', row[4].strip())])
            if not p_ids:
                raise exceptions.Warning(_('Any product found with CN %s')
                                         % row[4])

            zip_ids = zip_env.search([('name', '=', row[2].strip())])
            if not zip_ids:
                raise exceptions.Warning(_('Zip %s not found') % row[2])

            if not zip_ids[0].agent_id:
                raise exceptions.Warning(_('Zip %s didn\'t have agent set')
                                         % row[2])

            pharma_env.create({'pharmacy_name': row[0],
                               'pharmacy_street': row[1],
                               'pharmacy_zip': row[2],
                               'pharmacy_location': row[3],
                               'product_cn': row[4],
                               'product_qty': row[6],
                               'product_id': p_ids[0].id,
                               'agent_id': zip_ids[0].agent_id.id,
                               'date': imp_date,
                               'price_unit': p_ids[0].price,
                               'price_subtotal': p_ids[0].price * row[6]
                               })
