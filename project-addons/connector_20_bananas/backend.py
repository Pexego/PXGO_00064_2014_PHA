# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.addons.connector.backend as backend

bananas = backend.Backend("bananas")

bananas15 = backend.Backend(parent=bananas, version="1.6")
