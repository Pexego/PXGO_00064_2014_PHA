# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
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
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    docs_confirmed = fields.Boolean(default=False)
    docs_confirmed_check = fields.Boolean(compute='_docs_confirmed_check')

    def _docs_confirmed_check(self):
        for rec in self:
            rec.docs_confirmed = rec.docs_confirmed or not \
                bool(rec.partner_id.country_id.sales_abroad_id)
            rec.docs_confirmed_check = rec.docs_confirmed

    @api.multi
    def pre_transfer_checks(self):
        sp = self.browse(self.ids)
        country_id = sp.partner_id.country_id.id
        reference = sp.name
        return self.env['sales.abroad.confirm.docs'].wizard_view(country_id,
                                                                 reference)


class stock_move(models.Model):
    _inherit = 'stock.move'
    docs_confirmed = fields.Boolean(default=False)
    docs_confirmed_check = fields.Boolean(compute='_docs_confirmed_check')

    def _docs_confirmed_check(self):
        for rec in self:
            rec.docs_confirmed = rec.docs_confirmed or \
                rec.picking_id.docs_confirmed_check
            rec.docs_confirmed_check = rec.docs_confirmed

    @api.multi
    def pre_move_checks(self):
        sp = self.browse(self.ids).picking_id
        country_id = sp.partner_id.country_id.id
        reference = sp.name
        return self.env['sales.abroad.confirm.docs'].wizard_view(country_id,
                                                                 reference)


class stock_picking_wave(models.Model):
    _inherit = 'stock.picking.wave'
    docs_confirmed = fields.Boolean(default=False)
    docs_confirmed_check = fields.Boolean(compute='_docs_confirmed_check')

    def _docs_confirmed_check(self):
        for pw in self:
            pw.docs_confirmed = True
            for pl in pw.picking_ids:
                pw.docs_confirmed = pw.docs_confirmed and \
                    pl.docs_confirmed_check
            pw.docs_confirmed_check = pw.docs_confirmed

    @api.multi
    def pre_wave_checks(self):
        if not self.docs_confirmed_check:
            raise Warning(_("Please, check the documents of all picking lines."))
