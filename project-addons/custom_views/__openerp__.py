# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus All Rights Reserved
#    $Marcos Ybarra<marcos.ybarra@pharmadus.com>$
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
{
    'name': "Custom views",
    'version': '1.0',
    'category': '',
    'summary' : 'Custom views',
    'description': " //static/description/index.html//",
    'author': 'Pharmadus I+D+i',
    'website': 'www.pharmadus.com',
    'depends' : [
        'base',
        'sale',
        'purchase',
        'purchase_analytic_plans',
        'sale_commission',
        'sale_samples',
        'newclient_review',
        'pre_customer',
        'partner_prospect',
        'stock',
        'custom_permissions',
        'return_out_of_date',
        'product_stock_unsafety',
    ],
    'data' : [
        'views/sale_view.xml',
        'views/custom_css.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml',
        'views/purchase_view2.xml',
        'views/stock_quant.xml',
        'views/stock_view.xml',
        'views/view_form_custom.xml',
        'views/purchase_analytics_plan_view.xml',
        'views/account_invoice_view.xml',
        'views/hr_expense_custom_view.xml',
        'views/account_payment_view.xml',
        'views/hr_holidays_view.xml',
        'views/product_stock_unsafety_view.xml',
        'wizard/payment_order_create_view.xml',
        'wizard/return_product.xml',
        'data/wizards_units_precision.xml',
        'security/menus.xml',
    ],
    'installable': True
}
