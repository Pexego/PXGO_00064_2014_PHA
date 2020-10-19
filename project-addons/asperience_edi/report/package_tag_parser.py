# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class PackageTagParser(models.AbstractModel):
    """"""

    _name = "report.asperience_edi.package_tag_report"

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env["report"]
        pick_obj = self.env["stock.picking"]
        report_name = "asperience_edi.package_tag_report"
        if not data:
            raise except_orm(_("Error"), _("You must print it from a wizard"))

        pick = pick_obj.browse(data["pick_id"])
        num_packs = 0
        pack_list = []
        for op in pick.pack_operation_ids:
            pack = 0
            if op.package and op.package not in pack_list:
                pack = 1
                pack_list.append(op.package)
            num_packs += op.complete + pack
        docargs = {
            "doc_ids": [],
            "doc_model": "stock.picking",
            "docs": pick,
            "num_packs": num_packs,
        }
        return report_obj.render(report_name, docargs)
