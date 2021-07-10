# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Marcos Ybarra<marcos.ybarra@pharmadus.com>$
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
    'name': "Custom permissions",
    'version': '1.0',
    'category': '',
    'summary' : ' Various modifications for show just what is needed and customize views to delete or add some fields',
    'description': " //static/description/index.html//",
    'author': 'Pharmadus I+D+i',
    'website': 'www.pharmadus.com',
    'depends' : [
                 'hr_expense',
                 'crm',
                 'sale',
                 'stock',
                 'sale_commission',
                 'hr',
                 'hr_holidays',
                 'sale_channel',
                 'product',
                 'mrp',
                 'custom_sale_commission',
                 'delivery',
                 'portal_sale',
                 'sale_channel',
                 'project',
                 'return_out_of_date',
                 'sale_transfer_sample_rel',
                 'crm_claim'],
    'data' : ['security/groups.xml',
              'views/crm_phone_call.xml',
              'views/crm_claim_view.xml',
              'views/partner_followup.xml',
              'views/sale_view.xml',
              'views/res_groups_view.xml',
              'views/sale_view_salesmanph.xml',
              'views/partner_view.xml',
              'views/res_partner_view.xml',
              'views/account_report.xml',
              'views/product_view.xml',
              'views/css_custom.xml',
              'views/account_analytic_plans.xml',
              'data/hr_holidays_workflow.xml',
              'security/record_rules.xml',
              'security/menus.xml',
              'security/ir.model.access.csv'],
    'installable': True
}
