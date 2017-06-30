# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
from openerp import models, fields, api, _, exceptions


class release(models.TransientModel):

    _name = "mrp.partial.release"
    release_percent = fields.Float('Release percentage')
    release_qty = fields.Float('Release Quantity')
    reason = fields.Char('Reason', required=True)

    @api.onchange('release_percent')
    def onchange_release_percentage(self):
        if self.release_percent > 100:
            self.release_percent = 100
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False))
        total = sum([x.product_uom_qty for x in production.move_created_ids])
        if total:
            self.release_qty = total * (self.release_percent / 100)
        else:
            raise exceptions.Warning(_('Release error'),
                                     _('Production alredery completed'))

    @api.onchange('release_qty')
    def onchange_release_qty(self):
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False))
        for depends_lot in production.final_lot_id.state_depends:
            if depends_lot.state != 'approved':
                raise exceptions.Warning(
                    _('material lot error'),
                    _('Material lot %s not approved') % depends_lot.name)
        total = sum([x.product_uom_qty for x in production.move_created_ids])
        if total:
            if self.release_qty > total:
                self.release_qty = total
            self.release_percent = (self.release_qty / total) * 100
        else:
            raise exceptions.Warning(_('Release error'),
                                     _('Production alredery completed'))

    @api.multi
    def release(self):
        produce_wiz = self.env['mrp.product.produce'].create(
            {'mode': 'only_produce'})
        produce_wiz.product_qty = self.release_qty
        produce_wiz.consume_lines = False
        produce_wiz.with_context(ignore_child=True).do_produce()
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False))
        self.env['mrp.partial.release.log'].create_release_log(production,
                                                               self)
        return True
