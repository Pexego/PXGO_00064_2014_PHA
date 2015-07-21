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

from openerp import tools, models, fields
import openerp.addons.decimal_precision as dp


class MrpIndicatorsBaseReport(models.Model):

    _name = "mrp.indicators.base.report"
    _auto = False
    _order = 'date desc'

    date = fields.Date('Date', readonly=True)
    final_lot_id = fields.Many2one('stock.production.lot', 'Lot',
                                   readonly=True)
    qty = fields.Float('Qty.', readonly=True, digits=dp.
                       get_precision('Product Unit of Measure'))
    prod_ratio = fields.Float('Production ratio', readonly=True)
    container_id = fields.Many2one('product.container', 'Container',
                                   readonly=True)
    year = fields.Char('Year', size=4, readonly=True)
    month = fields.Selection([('01', 'January'), ('02', 'February'),
                              ('03', 'March'), ('04', 'April'), ('05', 'May'),
                              ('06', 'June'), ('07', 'July'), ('08', 'August'),
                              ('09', 'September'), ('10', 'October'),
                              ('11', 'November'), ('12', 'December')], 'Month',
                             readonly=True)
    day = fields.Char('Day', size=128, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    workcenter_id = fields.Many2one("mrp.workcenter", "Workcenter",
                                    readonly=True)
    routing_id = fields.Many2one("mrp.routing", "Routing", readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'mrp_indicators_base_report')
        cr.execute("""
create or replace view mrp_indicators_base_report as (
select mp.id,to_char(mp.date_planned, 'YYYY-MM-DD') as date,mp.final_lot_id,
wl.total_produced as qty, wl.prod_ratio, pt.container_id,
to_char(mp.date_planned, 'YYYY') as year,
to_char(mp.date_planned, 'MM') as month,
to_char(mp.date_planned, 'YYYY-MM-DD') as day, mp.company_id,
wl.workcenter_id, mp.routing_id from
mrp_production mp left join
(select distinct on (production_id) * from mrp_production_workcenter_line
order by production_id,sequence desc) wl
on mp.id =  wl.production_id
inner join product_product pp on pp.id = mp.product_id
inner join product_template pt on pp.product_tmpl_id = pt.id
where mp.final_lot_id is not null and mp.routing_id is not null)""")
