# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Modelo 347 AEAT (Pharmadus)",
    "version": "8.0.1.5.0",
    "category": "Localisation/Accounting",
    "website": "https://www.pharmadus.com",
    "author": "Pharmadus I.T.",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es_aeat_mod347",
        "custom_reports",
    ],
    "data": [
        "views/mod347_view.xml",
        "report/mod347_report.xml",
    ],
    "images": [
        "images/l10n_es_aeat_mod347.png",
    ],
}