# -*- coding: utf-8 -*-
from openerp import models, fields, api


class StockPaletReportSelector(models.TransientModel):
    _name = 'stock.palet.report.selector'

    @api.model
    def _default_report_type(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            picking_id = self.env['stock.picking'].browse(active_ids[0])
            return picking_id.partner_id.palet_report_type or 'normal'
        else:
            return 'normal'

    # Las opciones de este selector también están definidas en res.partner
    # por lo que, si las cambiamos, tenemos que actualizarlas allí también
    report_type = fields.Selection([
            ('normal', 'Normal'),
            ('gs1-128-1', 'GS1-128 (02-37-15-10-00)')
        ],
        string='Tipo de etiquetas a imprimir',
        default=lambda self: self._default_report_type(),
        required=True
    )

    @api.multi
    def print_report(self):
        paperformat_id = self.env. \
            ref('warehouse_shipping_light.paperformat_container_labels')

        if self.report_type == 'gs1-128-1':
            report_name = 'warehouse_shipping_light.' \
                          'report_palet_labels_gs1-128-1'
        else:  # Default report
            report_name = 'warehouse_shipping_light.report_palet_labels'

        ctx = dict(
            self.env.context or {},
            active_ids=self.env.context.get('active_ids'),
            active_model='stock.picking'
        )
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'paperformat_id': paperformat_id.id,
            'context': ctx
        }
