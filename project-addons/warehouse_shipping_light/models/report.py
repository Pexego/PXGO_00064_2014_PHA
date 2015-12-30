# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus. All Rights Reserved
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

from openerp import models, api


class wslReportExpeditions(models.AbstractModel):
    _name = 'report.warehouse_shipping_light.wsl_report_expeditions'

    @api.multi
    def render_html(self, data=None):
        model = u'stock.picking'
        pickings = self.env[model].browse(self._ids)
        docargs = {
            'doc_ids': self._ids,
            'doc_model': model,
            'docs': pickings,
        }
        # Update sent counter
        for p in pickings:
            p.sent += 1

        return self.env['report'].render(
                'warehouse_shipping_light.wsl_report_expeditions', docargs)