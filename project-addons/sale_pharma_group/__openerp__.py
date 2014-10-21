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

{
    'name': "Sale pharma groups",
    'version': '1.0',
    'category': 'sale',
    'description': """Customization to manage pharma groups commissions""",
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ['base',
                'sale',
                'sale_commission',
                'base_location',
                'sale_replacement',
                'product_pharma_fields'],
    "data": ['better_zip_view.xml',
             'wizard/assign_zip_agent_wizard_view.xml',
             'sale_agent_view.xml',
             'sale_order_view.xml',
             'res_partner_view.xml',
             'pharma_group_sale_view.xml',
             'wizard/import_pharma_group_sales_view.xml',
             'wizard/assign_agent_wizard_view.xml',
             'settlement_line_view.xml',
             'settlement_view.xml',
             'wizard/wizard_invoice_view.xml',
             'security/ir.model.access.csv'],
    "installable": True
}
