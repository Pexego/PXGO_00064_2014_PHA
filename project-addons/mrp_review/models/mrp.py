# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models, tools
from openerp.addons.product import _common
from openerp.osv import fields


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    _columns = {
        "state": fields.selection(
            [
                ("draft", "New"),
                ("cancel", "Cancelled"),
                ("confirmed", "Awaiting Raw Materials"),
                ("ready", "Ready"),
                ("in_production", "In production"),
                ("qty_set", "Final quantity set"),
                ("postposed_release", "Postposed release"),
                ("released", "Released"),
                ("done", "Done"),
            ],
            string="Status",
            readonly=True,
            track_visibility="onchange",
            copy=False,
            help="When the production order is created the status is set to 'Draft'.\n\
                If the order is confirmed the status is set to 'Waiting Goods'.\n\
                If any exceptions are there, the status is set to 'Picking Exception'.\n\
                If the stock is available then the status is set to 'Ready to Produce'.\n\
                When the production gets started then the status is set to 'In Production'.\n\
                When the production is over, the status is set to 'Done'.",
        ),
        "postposed_release": fields.boolean(copy=False),
        "routing_id": fields.many2one(
            "mrp.routing",
            string="Routing",
            on_delete="set null",
            readonly=True,
            states={
                "draft": [("readonly", False)],
                "confirmed": [("readonly", False)],
                "ready": [("readonly", False)],
            },
            help="The list of operations (list of work centers) to produce the finished product. The routing is mainly used to compute work center costs during operations and to plan future loads on work centers based on production plannification.",
        ),
    }

    @api.multi
    def prod_act_postpose_release(self):
        return self.write(
            {"state": "postposed_release", "postposed_release": True}
        )

    @api.multi
    def prod_act_final_qty(self):
        return self.write({"state": "qty_set"})

    @api.multi
    def prod_act_release(self):
        return self.write({"state": "released"})

    @api.model
    def _make_production_produce_line(self, production):
        prod_name = production.name
        procurement_group = self.env["procurement.group"].search(
            [("name", "=", prod_name)], limit=1
        )
        if not procurement_group:
            procurement_group = self.env["procurement.group"].create(
                {"name": prod_name}
            )
        self = self.with_context(set_push_group=procurement_group.id)
        return super(MrpProduction, self)._make_production_produce_line(
            production
        )

    @api.multi
    def write(self, vals, update=True, mini=True):
        def _factor(factor, product_efficiency, product_rounding):
            factor = factor / (product_efficiency or 1.0)
            factor = _common.ceiling(factor, product_rounding)
            if factor < product_rounding:
                factor = product_rounding
            return factor

        res = super(MrpProduction, self).write(vals, update, mini)
        for prod in self:
            if vals.get("routing_id") and vals.get("state", prod.state) in (
                "confirmed",
                "ready",
            ):
                result = []
                bom = prod.bom_id
                factor = self.env["product.uom"]._compute_qty(
                    prod.product_uom.id, prod.product_qty, bom.product_uom.id
                )
                factor = _factor(
                    factor, bom.product_efficiency, bom.product_rounding
                )
                routing = self.env["mrp.routing"].browse(vals["routing_id"])
                if routing:
                    for wc_use in routing.workcenter_lines:
                        wc = wc_use.workcenter_id
                        d, m = divmod(
                            factor, wc_use.workcenter_id.capacity_per_cycle
                        )
                        mult = d + (m and 1.0 or 0.0)
                        cycle = mult * wc_use.cycle_nbr
                        result.append(
                            {
                                "name": tools.ustr(wc_use.name)
                                + " - "
                                + tools.ustr(
                                    bom.product_tmpl_id.name_get()[0][1]
                                ),
                                "workcenter_id": wc.id,
                                "sequence": (wc_use.sequence or 0),
                                "cycle": cycle,
                                "hour": float(
                                    wc_use.hour_nbr * mult
                                    + (
                                        (wc.time_start or 0.0)
                                        + (wc.time_stop or 0.0)
                                        + cycle * (wc.time_cycle or 0.0)
                                    )
                                    * (wc.time_efficiency or 1.0)
                                ),
                            }
                        )
                prod.write(
                    {"workcenter_lines": [(5,)] + [(0, 0, x) for x in result]}
                )
        return res
