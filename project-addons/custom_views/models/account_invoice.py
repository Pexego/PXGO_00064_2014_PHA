# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields, _, exceptions
from openerp.exceptions import Warning
import datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    latest_calculations = fields.Datetime(
            'Latest date and time when amounts were calculated')
    banking_mandate_needed = fields.Boolean(
            related='payment_mode_id.banking_mandate_needed')
    payment_document_delivered = fields.Boolean(default=False)
    payment_document_date = fields.Datetime()
    payment_date_planned = fields.Date()
    partner_vat = fields.Char(related='partner_id.vat', readonly=True)
    partner_vat_liens = fields.Char(related='partner_id.vat', readonly=True)
    partner_liens = fields.Boolean(related='partner_id.liens')
    partner_insured = fields.Boolean(related='partner_id.insured')
    credit = fields.Float(compute='_get_credit')
    debit = fields.Float(compute='_get_debit')
    partner_parent_category_id = fields.Many2one(
        comodel_name='res.partner.category',
        compute='_get_partner_parent_category')
    payment_mode_bank_id = fields.Many2one(related='payment_mode_id.bank_id')

    @api.one
    def _get_partner_parent_category(self):
        c = self.partner_id.category_id
        if c and c.parent_id:
            self.partner_parent_category_id = c.parent_id
        elif c:
            self.partner_parent_category_id = c

    @api.one
    def _get_credit(self):
        self.credit = self.amount_total if self.type in \
                                             ('out_refund', 'in_invoice') else 0

    @api.one
    def _get_debit(self):
        self.debit = self.amount_total if self.type in \
                                            ('out_invoice', 'in_refund') else 0

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(type, partner_id,
                date_invoice, payment_term, partner_bank_id, company_id)
        partner = self.env['res.partner'].browse(partner_id)

        payment_mode_id = res['value'].get('payment_mode_id')
        if payment_mode_id:
            payment_mode = self.env['payment.mode'].browse(payment_mode_id)
            if payment_mode.banking_mandate_needed:
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

        if type == 'out_refund' and partner.customer_payment_mode:
            res['value'].update({
                'payment_mode_id': partner.customer_payment_mode.id
            })

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

        if vals.get('payment_document_delivered', False):
            vals['payment_document_date'] = fields.Datetime.now()
        else:
            vals['payment_document_date'] = False

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

        if 'payment_document_delivered' in vals:
            if vals.get('payment_document_delivered', False):
                vals['payment_document_date'] = fields.Datetime.now()
            else:
                vals['payment_document_date'] = False

        # Force re-calculations on save
        re_calculate = False
        type_is_out_invoice = True
        if not vals.get('latest_calculations'):
            for rec in self:
                now = datetime.datetime.now()
                if rec.latest_calculations:
                    then = fields.Datetime.from_string(rec.latest_calculations)
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

    @api.multi
    def duplicate(self):
        res = self.copy()

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': res.id,
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
            'nodestroy': True,
            'context': self.env.context
        }

    @api.multi
    def clear_mandate(self):
        self.mandate_id = False


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


class AccountInvoiceConfirm(models.TransientModel):
    _inherit = 'account.invoice.confirm'

    @api.multi
    def invoice_confirm(self):
        invoice_ids = self.env.context.get('active_ids', [])
        invoices = self.env['account.invoice'].browse(invoice_ids)
        orphan_invoices = []
        for invoice in invoices:
            if invoice.payment_mode_id and \
               invoice.payment_mode_id.banking_mandate_needed and \
               not invoice.mandate_id:
                orphan_invoices.append(invoice)

        if len(orphan_invoices) > 0:
            invoice_list = '\n'.join([x.origin if x.origin \
                                               else x.partner_id.name \
                                      for x in orphan_invoices])
            raise exceptions.Warning(_('The following invoices do not have the '
                                       'needed mandates assigned:\n%s' %
                                       invoice_list))

        return super(AccountInvoiceConfirm, self).invoice_confirm()
