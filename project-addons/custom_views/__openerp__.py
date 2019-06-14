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
        'account',
        'account_payment',
        'sale_channel',
        'sale_commission',
        'sale_samples',
        'newclient_review',
        'pre_customer',
        'partner_prospect',
        'stock',
        'mrp',
        'custom_permissions',
        'return_out_of_date',
        'product_stock_unsafety',
        'product_spec',
        'mass_editing',
    ],
    'data' : [
        'views/sale_view.xml',
        'views/custom_css.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml',
        'views/purchase_view.xml',
        'views/stock_view.xml',
        'views/view_form_custom.xml',
        'views/purchase_analytics_plan_view.xml',
        'views/account_invoice_view.xml',
        'views/hr_expense_custom_view.xml',
        'views/account_payment_view.xml',
        'views/hr_holidays_view.xml',
        'views/mrp_view.xml',
        'views/mass_editing_view.xml',
        'views/product_pricelist_view.xml',
        'views/account_move_line_view.xml',
        'views/return_reason_view.xml',
        'wizard/payment_order_create_view.xml',
        'wizard/return_product.xml',
        'wizard/product_stock_unsafety_view.xml',
        'wizard/warning_message.xml',
        'wizard/cancel_picking_confirmation_view.xml',
        'wizard/account_invoice_special.xml',
        'wizard/purchasable_products_view.xml',
        'wizard/product_incoming_parameters_view.xml',
        'wizard/deactivate_product_view.xml',
        'data/remove_old_translations.xml',
        'data/wizards_units_precision.xml',
        'data/mrp_procedure_type.xml',
        'data/ir_rule.xml',
        'data/return_reason.xml',
        'data/ir_actions_server.xml',
        'data/ir_cron.xml',
        'security/menus.xml',
        'security/buttons.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
