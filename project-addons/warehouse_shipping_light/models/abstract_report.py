# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
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
from openerp.exceptions import Warning
from openerp.tools.translate import _


class wslReportExpeditions(models.AbstractModel):
    _name = 'report.warehouse_shipping_light.wsl_report_expeditions'

    @api.multi
    def render_html(self, data=None):
        model = u'stock.expeditions'
        expeditions = self.env[model].browse(self._ids)
        docargs = {
            'doc_ids': self._ids,
            'doc_model': model,
            'docs': expeditions,
        }
        # Update sent counter
        for e in expeditions:
            e.sent += 1

        return self.env['report'].render(
                'warehouse_shipping_light.wsl_report_expeditions', docargs)


class wslReportPickingNote(models.AbstractModel):
    _name = 'report.warehouse_shipping_light.wsl_report_picking'

    @api.multi
    def render_html(self, data=None):
        model = u'stock.picking'
        pickings = self.env[model].browse(self._ids)

        if pickings:
            if pickings[0].state not in ['partially_available', 'assigned', 'done']:
                raise Warning(_('You must confirm availability of this picking note first!'))

        docargs = {
            'doc_ids': self._ids,
            'doc_model': model,
            'docs': pickings,
        }
        return self.env['report'].render(
                'warehouse_shipping_light.wsl_report_picking', docargs)


class wslReportDeliveryNote(models.AbstractModel):
    _name = 'report.warehouse_shipping_light.wsl_report_delivery_note'

    @api.multi
    def render_html(self, data=None):
        model = u'stock.picking'
        pickings = self.env[model].browse(self._ids)

        if pickings:
            if pickings[0].state != 'done':
                raise Warning(_('You must transfer this picking note first!'))
            if not pickings[0].sale_id:
                raise Warning(_('This report is only available for outgoing orders'))

        docargs = {
            'doc_ids': self._ids,
            'doc_model': model,
            'docs': pickings,
        }
        return self.env['report'].render(
                'warehouse_shipping_light.wsl_report_delivery_note', docargs)


class wslReportContainerLabels(models.AbstractModel):
    _name = 'report.warehouse_shipping_light.report_container_labels'

    @api.multi
    def render_html(self, data=None):
        model = u'stock.picking'
        pickings = self.env[model].browse(self._ids)

        if pickings and pickings[0].state != 'done':
            raise Warning(_('You must transfer this picking note first!'))

        if not pickings or not pickings[0].number_of_packages:
            raise Warning(_('No container labels to print!'))

        docargs = {
            'doc_ids': self._ids,
            'doc_model': model,
            'docs': pickings,
        }
        return self.env['report'].render(
                'warehouse_shipping_light.report_container_labels', docargs)


class wslReportPaletLabels(models.AbstractModel):
    _name = 'report.warehouse_shipping_light.report_palet_labels'

    @api.multi
    def render_html(self, data=None):
        model = u'stock.picking'
        pickings = self.env[model].browse(self._ids)

        if pickings and pickings[0].state != 'done':
            raise Warning(_('You must transfer this picking note first!'))

        if not pickings or not pickings[0].number_of_palets:
            raise Warning(_('No palet labels to print!'))

        docargs = {
            'doc_ids': self._ids,
            'doc_model': model,
            'docs': pickings,
        }
        return self.env['report'].render(
                'warehouse_shipping_light.report_palet_labels', docargs)
