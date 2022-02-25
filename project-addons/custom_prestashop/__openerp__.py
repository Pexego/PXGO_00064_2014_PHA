# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Prestashop customizations",
    "version": "8.0.1.0.0",
    "author": "Comunitea",
    "license": "AGPL-3",
    "depends": [
        "connector_prestashop",
        "product_pack"
    ],
    "data": [
        "views/prestashop_backend.xml",
        "views/prestashop_shop.xml",
        "data/product.xml",
        "views/product.xml",
        "views/delivery_carrier.xml",
        "views/payment_method.xml",
        "views/account_fiscal_position.xml",
        "wizard/prestashop_import_product.xml",
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
