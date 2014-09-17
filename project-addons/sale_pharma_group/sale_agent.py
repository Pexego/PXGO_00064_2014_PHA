# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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

from openerp import models, fields


class commission_bussines_line(models.Model):

    _name = 'commission.bussines.line'

    name = fields.Char('Name', size=64, required=True)
    type = fields.Selection((('fijo', 'Fix percentage'),
                             ('tramos', 'By sections')), 'Type',
                             required=True, default='fijo')
    fix_qty = fields.Float('Fix Percentage')
    sections = fields.One2many('commission.section',
                                'commission_id', 'Sections')
    bussiness_line_id = fields.Many2one('account.analytic.account',
                                         'bussiness line')
    commission_id = fields.Many2one('commission', 'Commission')

    def calcula_tramos(self, cr, uid, ids, base):
        commission = self.browse(cr, uid, ids)[0]
        for section in commission.sections:
            if abs(base) >= section.commission_from and (
                    abs(base) <
                    section.commission_until or section.commission_until == 0):
                res = base * section.percent / 100.0
                return res
        return 0.0


class commission_section(models.Model):

    _inherit = "commission.section"

    commission_id = fields.Many2one('commission.bussines.line', 'Commission',
                                     required=True)

class commission(models.Model):
    """Objeto comisión"""

    _inherit = "commission"
    commission_line_id = fields.One2many('commission.bussines.line',
                                           'commission_id', 'commissions')
    type = fields.Selection((('fijo', 'Fix percentage'),
                                 ('tramos', 'By sections')), 'Type',
                                 required=False)

class SaleAgent(models.Model):

    _inherit = "sale.agent"

    related_zip_ids = fields.One2many('res.better.zip', 'agent_id',
                                      string="Zips", readonly=True)

    commission_group = fields.Float('Default commission group', default=10)
