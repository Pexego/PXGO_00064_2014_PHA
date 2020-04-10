# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from datetime import datetime, timedelta


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.multi
    def check_raw_material_alert_date(self):
        months_ahead = self.env.user.company_id.lot_alert_date_months_ahead
        months_ahead = datetime.today() + timedelta(days=+months_ahead * 30)
        months_ahead = fields.Datetime.to_string(months_ahead)
        raw_material_category_id = self.env.ref('__export__.product_category_9')
        alert_date_lot_ids = self.search([
            ('alert_date', '<', months_ahead),
            ('product_id.categ_id', '=', raw_material_category_id.id),
            ('quant_ids.location_id.usage', 'in', ('internal', 'view'))
        ], order='alert_date')

        if alert_date_lot_ids:
            warnings = u"""
                <style>
                    #avisos {
                        border-collapse: collapse;
                    }
                    #avisos td,
                    #avisos th {
                        border: 1px solid grey;
                        padding: 2px;
                    }
                </style>            
                <table id=\"avisos\">
                    <tr>
                        <th>Materia prima</th>
                        <th>Lote</th>
                        <th>Estado</th>
                        <th>Fecha alerta</th>
                    </tr>
            """

            states = {
                'draft': 'Nuevo',
                'in_rev': 'En revisión (Q)',
                'revised': 'Revisado',
                'approved': 'Aprobado',
                'rejected': 'Rechazado',
            }
            for lot_id in alert_date_lot_ids:
                warnings += u'<tr><td>{}</td><td>{}</td><td>{}</td>' \
                            u'<td>{}</td></tr>'.format(
                    lot_id.product_id.name,
                    lot_id.name,
                    states[lot_id.state],
                    lot_id.alert_date[:10]
                )
            warnings += u'</table>'

            template_id = self.env.\
                ref('mail_ph.raw_material_alert_date_mail_template')
            mail_id = template_id.send_mail(alert_date_lot_ids[0].id,
                                            force_send=False)
            mail_id = self.env['mail.mail'].browse(mail_id)
            mail_id.body_html += warnings

    @api.multi
    def check_product_use_date(self):
        months_ahead = self.env.user.company_id.lot_use_date_months_ahead
        months_ahead = datetime.today() + timedelta(days=+months_ahead * 30)
        months_ahead = fields.Datetime.to_string(months_ahead)
        product_category_ids = (
            self.env.ref('.prodcat023').id,
            self.env.ref('__export__.product_category_1525').id,
            self.env.ref('__export__.product_category_1494').id,
            self.env.ref('__export__.product_category_1493').id,
            self.env.ref('product.product_category_1').id
        )
        use_date_lot_ids = self.search([
            ('use_date', '<', months_ahead),
            ('product_id.categ_id', 'in', product_category_ids),
            ('quant_ids.location_id.usage', 'in', ('internal', 'view'))
        ], order='use_date')

        if use_date_lot_ids:
            warnings = u"""
                <style>
                    #avisos {
                        border-collapse: collapse;
                    }
                    #avisos td,
                    #avisos th {
                        border: 1px solid grey;
                        padding: 2px;
                    }
                </style>            
                <table id=\"avisos\">
                    <tr>
                        <th>Producto</th>
                        <th>Lote</th>
                        <th>Estado</th>
                        <th>Consumo preferente</th>
                    </tr>
            """

            states = {
                'draft': 'Nuevo',
                'in_rev': 'En revisión (Q)',
                'revised': 'Revisado',
                'approved': 'Aprobado',
                'rejected': 'Rechazado',
            }
            for lot_id in use_date_lot_ids:
                warnings += u'<tr><td>{}</td><td>{}</td><td>{}</td>' \
                            u'<td>{}</td></tr>'.format(
                    lot_id.product_id.name,
                    lot_id.name,
                    states[lot_id.state],
                    lot_id.use_date[:10]
                )
            warnings += u'</table>'

            template_id = self.env.ref('mail_ph.product_use_date_mail_template')
            mail_id = template_id.send_mail(use_date_lot_ids[0].id,
                                            force_send=False)
            mail_id = self.env['mail.mail'].browse(mail_id)
            mail_id.body_html += warnings