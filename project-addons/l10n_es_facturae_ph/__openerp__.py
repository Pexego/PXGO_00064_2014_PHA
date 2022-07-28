# -*- coding: utf-8 -*-
# © 2022 Pharmadus Botanicals
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Creación de Factura-e (FACe) (PH)',
    'version': '8.0.1.0.0',
    'author': 'ASR-OSS, '
              'FactorLibre, '
              'Tecon, '
              'Pexego, '
              'Malagatic, '
              'Comunitea, '
              'Odoo Community Association (OCA), '
              'Pharmadus Botanicals',
    'category': 'Accounting & Finance',
    'website': 'https://github.com/OCA/l10n-spain',
    'license': 'AGPL-3',
    'depends': ['l10n_es_facturae'],
    'installable': True,
    'data': [
        'views/account_invoice_view.xml',
        'wizard/facturae_invoice_lines_wizard.xml',
        'security/ir.model.access.csv',
    ],
}
