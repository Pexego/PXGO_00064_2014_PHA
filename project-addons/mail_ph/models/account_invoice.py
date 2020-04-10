# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions
from ..validations import is_valid_email
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


class AccountInvoiceOverDueNoticeSent(models.Model):
    _name = 'account.invoice.over.due.notice.sent'

    invoice_id = fields.Many2one(comodel_name='account.invoice')
    days_notified = fields.Integer(default=0)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    over_due_notice_sent = fields.One2many(
        comodel_name='account.invoice.over.due.notice.sent',
        inverse_name='invoice_id'
    )

    @api.multi
    def check_unpaid(self):
        logger.info('Unpaid invoices: Searching for...')

        company_id = self.env.user.company_id
        first_notice_days = company_id.over_due_first_notice_days
        second_notice_days = company_id.over_due_second_notice_days
        third_notice_days = company_id.over_due_third_notice_days

        today = date.today()
        notify_date = today + timedelta(days=-first_notice_days)
        notify_date = fields.Date.to_string(notify_date)
        unpaid_inv_ids = self.search([
            ('state', '=', 'open'),
            ('payment_document_delivered', '=', False),
            ('type', '=', 'out_invoice'),
            ('date_due', '<=', notify_date)
        ])
        aData = []
        for invoice_id in unpaid_inv_ids:
            aData.append([
                invoice_id,
                fields.Date.from_string(invoice_id.date_due),
                invoice_id.over_due_notice_sent.days_notified if \
                    invoice_id.over_due_notice_sent else 0
            ])
        del unpaid_inv_ids

        logger.info('Unpaid invoices: Calculating notice type based on days over...')
        notify_inv_ids = self.env['account.invoice']
        notice_model = self.env['account.invoice.over.due.notice.sent']
        for data in aData:
            days_passed = (today - data[1]).days
            notice_days = 0
            if days_passed >= third_notice_days and \
                    data[2] < third_notice_days:
                notice_days = third_notice_days
            elif days_passed >= second_notice_days and \
                    data[2] < second_notice_days:
                notice_days = second_notice_days
            elif days_passed >= first_notice_days and \
                    data[2] < first_notice_days:
                notice_days = first_notice_days

            if notice_days:
                if data[0].over_due_notice_sent:
                    data[0].over_due_notice_sent.\
                        write({'days_notified': notice_days})
                else:
                    notice_model.create({
                        'invoice_id': data[0].id,
                        'days_notified': notice_days
                    })
                notify_inv_ids += data[0]

        logger.info('Unpaid invoices: Sending mails...')
        notify_inv_ids.send_notice_email()
        logger.info('Unpaid invoices: Mails sent to pool')

    @api.multi
    def send_notice_email(self):
        template_id = self.env.ref('mail_ph.unpaid_invoice_mail_template')
        for invoice_id in self:
            commercial_mail = invoice_id.commercial_partner_id.email_to_send_invoice
            shipping_mail = invoice_id.partner_shipping_id.email_to_send_invoice
            if is_valid_email(shipping_mail) or is_valid_email(commercial_mail):
                template_id.send_mail(invoice_id.id, force_send=False)

    @api.multi
    def send_customer_invoice_by_email(self):
        bad_emails = ''
        failed_to_send = ''
        separator = '--------------------------------------------------------'
        template_id = self.env.ref('mail_ph.customer_invoice_mail_template')
        for invoice_id in self:
            commercial_mail = invoice_id.commercial_partner_id.email_to_send_invoice
            shipping_mail = invoice_id.partner_shipping_id.email_to_send_invoice
            if is_valid_email(shipping_mail) or is_valid_email(commercial_mail):
                try:
                    template_id.send_mail(invoice_id.id, force_send=True)
                except:
                    failed_to_send += 'Factura nº: {}\n' \
                              'Cliente: {}\n' \
                              'e-mail dir. envío: {}\n' \
                              'e-mail dir. facturación:{}\n\n'.format(
                        invoice_id.number or 'S/N',
                        invoice_id.partner_id.name,
                        invoice_id.partner_shipping_id.email_to_send_invoice,
                        invoice_id.commercial_partner_id.email_to_send_invoice
                    )
            else:
                bad_emails += 'Factura nº: {}\n' \
                              'Cliente: {}\n' \
                              'e-mail dir. envío: {}\n' \
                              'e-mail dir. facturación:{}\n\n'.format(
                    invoice_id.number or 'S/N',
                    invoice_id.partner_id.name,
                    invoice_id.partner_shipping_id.email_to_send_invoice,
                    invoice_id.commercial_partner_id.email_to_send_invoice
                )

        if bad_emails + failed_to_send:
            if bad_emails:
                bad_emails = 'No tiene e-mail o es incorrecto:\n\n' + bad_emails
            if failed_to_send:
                failed_to_send = '\nEnvíos fallidos:\n\n' + failed_to_send
            if bad_emails and failed_to_send:
                warnings = bad_emails + separator + failed_to_send
            else:
                warnings = bad_emails + failed_to_send
            raise exceptions.Warning(warnings)
        else:
            raise exceptions.Warning('Todos los mensajes enviados correctamente')
