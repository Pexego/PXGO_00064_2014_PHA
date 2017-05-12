# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from openerp.exceptions import Warning
import datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    latest_calculations = fields.Datetime(
            'Latest date and time when amounts were calculated')
    banking_mandate_needed = fields.Boolean(
            related='payment_mode_id.banking_mandate_needed')

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(type, partner_id,
                date_invoice, payment_term, partner_bank_id, company_id)
        payment_mode_id = res['value'].get('payment_mode_id')
        if payment_mode_id:
            payment_mode = self.env['payment.mode'].browse(payment_mode_id)
            if payment_mode.banking_mandate_needed:
                partner = self.env['res.partner'].browse(partner_id)
                if not partner.bank_ids and partner.parent_id.bank_ids:
                    banks = partner.parent_id.bank_ids
                else:
                    banks = partner.bank_ids
                if banks:
                    mandates = []
                    for bank in banks:
                        for mandate in bank.mandate_ids:
                            mandates.append(mandate)
                    if len(mandates) == 1:
                        mandate_id = mandates[0].id
                    else:
                        mandate_id = False
                else:
                    mandate_id = False
            else:
                mandate_id = False
        else:
            mandate_id = False
        res['value'].update({'mandate_id': mandate_id})
        return res

    @api.multi
    @api.onchange('payment_mode_id')
    def _search_banking_mandate(self):
        # Check if banking mandate is needed and populate it if the partner has
        # one and only one. If the partner has several mandates, the view will
        # force the user to choose one.
        for invoice in self:
            if invoice.payment_mode_id and \
               invoice.payment_mode_id.banking_mandate_needed:
                # If the partner has not a bank and has a parent partner,
                # check parent's bank(s) instead
                partner = invoice.partner_id
                if not partner.bank_ids and partner.parent_id.bank_ids:
                    banks = partner.parent_id.bank_ids
                else:
                    banks = partner.bank_ids
                if banks:
                    mandates = []
                    for bank in banks:
                        for mandate in bank.mandate_ids:
                            mandates.append(mandate)
                    if len(mandates) == 1:
                        invoice.mandate_id = mandates[0]
                    else:
                        invoice.mandate_id = False
                else:
                    invoice.mandate_id = False
            else:
                invoice.mandate_id = False

    @api.model
    def create(self, vals):
        # Check for unique supplier reference, before create invoice
        self._check_unique_reference(vals.get('reference'),
                                     vals.get('partner_id'),
                                     vals.get('date_invoice'))
        res = super(AccountInvoice, self).create(vals)
        # Search if it needs automatic assignment of banking mandates and
        # triggers write event to force re-calculations after invoice creation
        res._search_banking_mandate()
        return res

    @api.multi
    def write(self, vals):
        # Check for unique supplier reference
        for invoice in self:
            reference = vals.get('reference', invoice.reference)
            partner = vals.get('partner_id', invoice.partner_id.id)
            date_invoice = vals.get('date_invoice', invoice.date_invoice)
            self._check_unique_reference(reference, partner, date_invoice)

        # Force re-calculations on save
        re_calculate = False
        type_is_out_invoice = True
        if not vals.get('latest_calculations'):
            for rec in self:
                now = datetime.datetime.now()
                if rec.latest_calculations:
                    then = datetime.datetime.strptime(rec.latest_calculations,
                                                      DATETIME_FORMAT)
                else:
                    then = now - datetime.timedelta(days=1)

                diff = now - then
                re_calculate = re_calculate or diff.total_seconds() > 10
                type_is_out_invoice = type_is_out_invoice and \
                                      (rec.type == 'out_invoice')

        if re_calculate and type_is_out_invoice:
            # Timestamp to avoid unnecessary loops
            vals['latest_calculations'] = fields.Datetime.now()
            res = super(AccountInvoice, self).write(vals)
            self.button_reset_taxes()
        else:
            res = super(AccountInvoice, self).write(vals)

        return res

    def _check_unique_reference(self, reference, partner_id, date_invoice):
        if reference and partner_id and date_invoice:
            year = fields.Date.from_string(date_invoice).year
            current_year_begin = fields.Date.to_string(datetime.date(year, 1, 1))
            current_year_end = fields.Date.to_string(datetime.date(year, 12, 31))
            invoice = self.env['account.invoice'].search(
                [
                    ('partner_id', '=', partner_id),
                    ('reference', '=', reference.strip()),
                    ('date_invoice', '>=', current_year_begin),
                    ('date_invoice', '<=', current_year_end)
                ])
            if invoice and (invoice not in self):
                raise Warning(_('Already exists an invoice for %s with '
                                'this reference %s') %
                              (invoice[0].partner_id.name, reference))

    @api.multi
    def action_date_assign(self):
        # This is the first step in workflow before invoice validation
        # Check if all invoice lines have tax field set
        invoices = []
        for invoice in self:
            for line in invoice.invoice_line:
                if (not line.invoice_line_tax_id) and (invoice not in invoices):
                    invoices.append(invoice)
        if len(invoices) > 0:
            msg = _('The following invoices have detail lines without tax set:')
            msg += '\n'
            for invoice in invoices:
                if invoice.number:
                    msg += '\n- ' + _('Invoice number: ') + invoice.number
                else:
                    msg += '\n- ' + _('Origin document: ') + invoice.origin
            raise Warning(msg)
        else:
            return super(AccountInvoice, self).action_date_assign()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    invoice_type = fields.Selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
        ], related='invoice_id.type')
    invoice_line_tax_id = fields.Many2many(required=True)  # Inherited field
    default_code = fields.Char(related='product_id.default_code')
    commercial_partner_id = fields.Many2one(comodel_name='res.partner',
                                    related='invoice_id.commercial_partner_id')
    date_invoice = fields.Date(related='invoice_id.date_invoice')

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):
        res = super(AccountInvoiceLine, self).product_id_change(product,
                uom_id, qty, name, type, partner_id, fposition_id, price_unit,
                currency_id, company_id)
        product_name = self.env['product.product'].browse(product).name_template
        res['value']['name'] = product_name
        return res
