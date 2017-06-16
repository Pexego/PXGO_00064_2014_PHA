# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Custom calendars',
    'version': '1.0',
    'category': 'mrp',
    'summary' : 'Bussines day calendars',
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': [
        'mrp',
    ],
    'data': [
        'wizards/calendar_wizard_view.xml',
        'views/mrp_calendar_view.xml',
        'views/base_calendar_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': ['static/src/xml/calendars.xml'],
    'installable': True
}