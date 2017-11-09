# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute("""DROP TABLE IF EXISTS product_analysis_method;""")
    cr.execute("""UPDATE product_analysis set method=NULL;""")
