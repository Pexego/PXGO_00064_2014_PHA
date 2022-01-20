# -*- coding: utf-8 -*-
# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# Copyright 2018 Luis M. Ontalba <luismaront@gmail.com>
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0
import datetime
import re

from openerp import models, api, fields, _
from openerp.exceptions import Warning as UserError
from openerp.tools import ormcache


class L10nEsVatBook(models.Model):
    _name = 'l10n.es.vat.book.backport'
    _inherit = "l10n.es.aeat.report"
    _aeat_number = 'LIVA'
    _period_yearly = True

    number = fields.Char(
        default="vat_book",
        readonly="True")

    line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        string='Issued/Received invoices',
        copy=False,
        readonly="True")

    issued_line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        domain=[('line_type', '=', 'issued')],
        string='Issued invoices',
        copy=False,
        readonly="True")

    rectification_issued_line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        domain=[('line_type', '=', 'rectification_issued')],
        string='Issued Refund Invoices',
        copy=False,
        readonly="True")

    received_line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        domain=[('line_type', '=', 'received')],
        string='Received invoices',
        copy=False,
        readonly="True")

    rectification_received_line_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.line',
        inverse_name='vat_book_id',
        domain=[('line_type', '=', 'rectification_received')],
        string='Received Refund Invoices',
        copy=False,
        readonly="True")

    calculation_date = fields.Date(
        string='Calculation Date')

    tax_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.tax.summary',
        string="Tax Summary",
        inverse_name='vat_book_id',
        readonly="True")

    issued_tax_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.tax.summary',
        string="Issued Tax Summary",
        inverse_name='vat_book_id',
        domain=[('book_type', '=', 'issued')],
        readonly="True")

    received_tax_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.tax.summary',
        string="Received Tax Summary",
        inverse_name='vat_book_id',
        domain=[('book_type', '=', 'received')],
        readonly="True")

    summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.summary',
        string="Summary",
        inverse_name='vat_book_id',
        readonly="True")

    issued_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.summary',
        string="Issued Summary",
        inverse_name='vat_book_id',
        domain=[('book_type', '=', 'issued')],
        readonly="True")

    received_summary_ids = fields.One2many(
        comodel_name='l10n.es.vat.book.summary',
        string="Received Summary",
        inverse_name='vat_book_id',
        domain=[('book_type', '=', 'received')],
        readonly="True")

    auto_renumber = fields.Boolean('Auto renumber invoices received',
                                   states={'draft': [('readonly', False)]})

    @api.model
    def _prepare_vat_book_tax_summary(self, tax_lines, book_type):
        tax_summary_data_recs = {}
        for tax_line in tax_lines:
            if tax_line.tax_id not in tax_summary_data_recs:
                tax_summary_data_recs[tax_line.tax_id] = {
                    'book_type': book_type,
                    'base_amount': 0.0,
                    'tax_amount': 0.0,
                    'total_amount': 0.0,
                    'tax_id': tax_line.tax_id.id,
                    'vat_book_id': self.id,
                    'special_tax_group': False
                }
            tax_summary_data_recs[tax_line.tax_id]['base_amount'] += \
                tax_line.base_amount
            tax_summary_data_recs[tax_line.tax_id]['tax_amount'] +=  \
                tax_line.tax_amount
            tax_summary_data_recs[tax_line.tax_id]['total_amount'] +=  \
                tax_line.total_amount
            if tax_line.special_tax_id:
                if tax_line.special_tax_id not in tax_summary_data_recs:
                    tax_summary_data_recs[tax_line.special_tax_id] = {
                        'book_type': book_type,
                        'base_amount': 0.0,
                        'tax_amount': 0.0,
                        'total_amount': 0.0,
                        'tax_id': tax_line.special_tax_id.id,
                        'vat_book_id': self.id,
                        'special_tax_group': tax_line.special_tax_group,
                    }

                tax_summary_data_recs[tax_line.special_tax_id]['base_amount'] += \
                    tax_line.base_amount
                tax_summary_data_recs[tax_line.special_tax_id]['tax_amount'] +=  \
                    tax_line.special_tax_amount
                tax_summary_data_recs[tax_line.special_tax_id]['total_amount'] +=  \
                    tax_line.base_amount + tax_line.special_tax_amount
        return tax_summary_data_recs

    @api.model
    def _create_vat_book_tax_summary(self, tax_summary_data_recs,
                                     tax_summary):
        for tax_id in tax_summary_data_recs.keys():
            self.env['l10n.es.vat.book.tax.summary'].create(
                tax_summary_data_recs[tax_id])
        return tax_summary

    def _prepare_vat_book_summary(self, tax_summary_recs, book_type):
        vals_list = []
        total_dic = {}
        for line in tax_summary_recs:
            if line.special_tax_group not in total_dic:
                total_dic[line.special_tax_group] = {
                    'base_amount': line.base_amount,
                    'tax_amount': line.tax_amount,
                    'total_amount': line.total_amount,
                }
            else:
                total_group = total_dic[line.special_tax_group]
                total_group['base_amount'] += line.base_amount
                total_group['tax_amount'] += line.tax_amount
                total_group['total_amount'] += line.total_amount
        for key, total_group in total_dic.items():
            vals_list.append({
                'book_type': book_type,
                'special_tax_group': key,
                'base_amount': total_group['base_amount'],
                'tax_amount': total_group['tax_amount'],
                'total_amount': total_group['total_amount'],
                'vat_book_id': self.id,
            })
        return vals_list

    @api.model
    def _create_vat_book_summary(self, tax_summary_recs, book_type):
        for vals in self._prepare_vat_book_summary(
                tax_summary_recs, book_type):
            self.env['l10n.es.vat.book.summary'].create(vals)

    def calculate(self):
        """
            Funcion call from vat_book
        """
        self._calculate_vat_book()
        return True

    def _prepare_book_line_vals(self, move_line, line_type):
        """
            This function make the dictionary to create a new record in issued
            invoices, Received invoices or rectification invoices

            Args:
                move_line (obj): move

            Returns:
                dictionary: Vals from the new record.
        """
        invoice = move_line.invoice_id
        partner = invoice.commercial_partner_id
        ref = invoice.number
        ext_ref = invoice.reference
        return {
            'line_type': line_type,
            'invoice_date': invoice.move_id.date,
            'partner_id': partner.id,
            'vat_number': partner.vat,
            'invoice_id': invoice.id,
            'ref': ref,
            'external_ref': ext_ref,
            'vat_book_id': self.id,
            'move_id': invoice.move_id.id,
            'tax_lines': {},
            'base_amount': 0.0,
            'special_tax_group': False,
        }

    @api.multi
    def _get_invoice_line_price_tax(self, invoice_line, tax):
        """Obtain the effective invoice line price after discount. Needed as
        we can modify the unit price via inheritance."""
        self.ensure_one()
        price = invoice_line._get_sii_line_price_unit()
        taxes = invoice_line.invoice_line_tax_id.\
            filtered(lambda x: x == tax or tax in x.child_ids).compute_all(
                price, invoice_line.quantity, product=invoice_line.product_id,
                partner=invoice_line.invoice_id.partner_id)
        amount = 0.0
        for tax in taxes['taxes']:
            amount += tax['amount']
        return amount

    def _prepare_book_line_tax_vals(self, move_line, vat_book_line, taxes):
        res = []
        sp_taxes_dic = self.get_special_taxes_dic()
        line_subtotal = move_line._get_sii_line_price_subtotal()
        if 'refund' in move_line.invoice_id.type:
            line_subtotal = -line_subtotal
        vat_book_line['base_amount'] += line_subtotal
        for tax in move_line.invoice_line_tax_id.\
                filtered(lambda x: (x in taxes or x.child_ids & taxes) and x.id
                         not in sp_taxes_dic):
            subtotal = line_subtotal
            amount_taxed = self._get_invoice_line_price_tax(move_line, tax)
            if 'refund' in move_line.invoice_id.type:
                subtotal = -subtotal
                amount_taxed = -amount_taxed
            tax_vals = {
                'tax_id': tax.id,
                'base_amount': subtotal,
                'tax_amount': amount_taxed,
                'total_amount': subtotal + amount_taxed,
                'move_line_ids': [(4, move_line.id)],
                'special_tax_group': False,
            }
            # must exists almost one special tax per line
            for stax in move_line.invoice_line_tax_id.\
                    filtered(lambda x: x.id in sp_taxes_dic):
                tax_group = sp_taxes_dic[stax.id]['special_tax_group']
                tax_vals['special_tax_group'] = tax_group
                tax_vals['special_tax_id'] = stax.id
                amount_taxed = self._get_invoice_line_price_tax(move_line,
                                                                stax)
                if 'refund' in move_line.invoice_id.type:
                    amount_taxed = -amount_taxed
                tax_vals['special_tax_amount'] = amount_taxed
                tax_vals['total_amount_special_include'] = \
                    subtotal + amount_taxed
                vat_book_line['special_tax_group'] = tax_group
            res.append(tax_vals)

        return res

    def upsert_book_line_tax(self, move_line, vat_book_line, taxes):
        vals = self._prepare_book_line_tax_vals(move_line, vat_book_line,
                                                taxes)
        tax_lines = vat_book_line['tax_lines']
        for tax_vals in vals:
            key = tax_vals['tax_id']
            if key not in tax_lines:
                tax_lines[key] = tax_vals.copy()
            else:
                tax_lines[key]['base_amount'] += tax_vals['base_amount']
                tax_lines[key]['tax_amount'] += tax_vals['tax_amount']
                tax_lines[key]['total_amount'] += tax_vals['total_amount']
                tax_lines[key]['move_line_ids'] += tax_vals['move_line_ids']
                if tax_vals.get('special_tax_group'):
                    tax_lines[key]['special_tax_amount'] += \
                        tax_vals['special_tax_amount']
                    tax_lines[key]['total_amount_special_include'] += \
                        tax_vals['total_amount_special_include']

    def _clear_old_data(self):
        """
            This function clean all the old data to make a new calculation
        """
        self.line_ids.unlink()
        self.summary_ids.unlink()
        self.tax_summary_ids.unlink()

    @ormcache()
    def get_pos_partner_ids(self):
        return self.env['res.partner'].with_context(active_test=False).search([
            ('aeat_anonymous_cash_customer', '=', True),
        ]).ids

    @ormcache()
    def get_special_taxes_dic(self):
        map_lines = self.env['aeat.vat.book.map.line'].search([
            ('special_tax_group', '!=', False),
        ])
        special_dic = {}
        for map_line in map_lines:
            for tax in map_line._get_vat_book_taxes_map(self.company_id):
                special_dic[tax.id] = {
                    'name': map_line.name,
                    'book_type': map_line.book_type,
                    'special_tax_group': map_line.special_tax_group,
                    'fee_type_xlsx_column': map_line.fee_type_xlsx_column,
                    'fee_amount_xlsx_column': map_line.fee_amount_xlsx_column,
                }
        return special_dic

    def get_book_line_key(self, move_line):
        return move_line.invoice_id.id

    def get_book_line_tax_key(self, move_line, tax):
        return move_line.move_id.id, move_line.invoice_id.id, tax.id

    def _set_line_type(self, line_vals, line_type):
        if line_vals['base_amount'] < 0.0:
            line_vals['line_type'] = 'rectification_{}'.format(line_type)

    def _check_exceptions(self, line_vals):
        if (not line_vals['vat_number'] and line_vals['partner_id'] not in
                self.get_pos_partner_ids()):
            line_vals['exception_text'] = _("Without VAT")

    def create_vat_book_lines(self, move_lines, line_type, taxes):
        VatBookLine = self.env['l10n.es.vat.book.line']
        moves_dic = {}
        for move_line in move_lines:
            line_key = self.get_book_line_key(move_line)
            if line_key not in moves_dic:
                moves_dic[line_key] = self._prepare_book_line_vals(
                    move_line, line_type)
            self.upsert_book_line_tax(move_line, moves_dic[line_key], taxes)
        for line_vals in moves_dic.values():
            tax_lines = line_vals.pop('tax_lines')
            tax_line_list = []
            tax_amount = 0.0
            for tax_line_vals in tax_lines.values():
                tax_amount += tax_line_vals['tax_amount']
                tax_line_list.append((0, 0, tax_line_vals))
            self._set_line_type(line_vals, line_type)
            line_vals.update({
                'total_amount': line_vals['base_amount'] + tax_amount,
                'tax_line_ids': [
                    (0, 0, vals) for vals in tax_lines.values()],
            })
            self._check_exceptions(line_vals)
            VatBookLine.create(line_vals)

    def _calculate_vat_book(self):
        """
            This function calculate all the taxes, from issued invoices,
            received invoices and rectification invoices
        """
        for rec in self:
            if not rec.company_id.partner_id.vat:
                raise UserError(
                    _("This company doesn't have VAT"))

            # clean the old records
            rec._clear_old_data()

            map_lines = self.env["aeat.vat.book.map.line"].search([])

            for map_line in map_lines.filtered(lambda x: not x.special_tax_group):
                taxes = map_line._get_vat_book_taxes_map(self.company_id)
                lines = map_line.get_invoice_lines(rec)
                rec.create_vat_book_lines(lines, map_line.book_type, taxes)

            # Issued
            book_type = 'issued'
            issued_tax_lines = rec.issued_line_ids.mapped(
                'tax_line_ids')
            rectification_issued_tax_lines = \
                rec.rectification_issued_line_ids.mapped(
                    'tax_line_ids')
            tax_summary_data_recs = rec._prepare_vat_book_tax_summary(
                issued_tax_lines + rectification_issued_tax_lines, book_type)
            rec._create_vat_book_tax_summary(
                tax_summary_data_recs, rec.issued_tax_summary_ids)
            rec._create_vat_book_summary(rec.issued_tax_summary_ids, book_type)

            # Received
            book_type = 'received'
            received_tax_lines = rec.received_line_ids.mapped(
                'tax_line_ids')
            rectification_received_tax_lines = \
                rec.rectification_received_line_ids.mapped(
                    'tax_line_ids')
            tax_summary_data_recs = rec._prepare_vat_book_tax_summary(
                received_tax_lines + rectification_received_tax_lines,
                book_type)
            rec._create_vat_book_tax_summary(
                tax_summary_data_recs, rec.received_tax_summary_ids)
            rec._create_vat_book_summary(rec.received_tax_summary_ids,
                                         book_type)

            # If we require to auto-renumber invoices received
            if rec.auto_renumber:
                rec_invs = self.env['l10n.es.vat.book.line'].search(
                    [('vat_book_id', '=', rec.id),
                     ('line_type', '=', 'received')],
                    order='invoice_date asc, ref asc')
                i = 1
                for rec_inv in rec_invs:
                    rec_inv.entry_number = i
                    i += 1
                rec_invs = self.env['l10n.es.vat.book.line'].search(
                    [('vat_book_id', '=', rec.id),
                     ('line_type', '=', 'rectification_received')],
                    order='invoice_date asc, ref asc')
                i = 1
                for rec_inv in rec_invs:
                    rec_inv.entry_number = i
                    i += 1
                # Write state and date in the report
            rec.write({
                'state': 'calculated',
                'calculation_date': fields.Datetime.now(),
            })

    def _format_date(self, date):
        # format date following user language
        lang_model = self.env['res.lang']
        lang = lang_model.search([('code', '=', self.env.user.lang)])
        date_format = lang.date_format
        return datetime.datetime.strftime(
            fields.Date.from_string(date), date_format)

    def get_report_file_name(self):
        return '{}{}C{}'.format(self.year, self.company_vat,
                                re.sub(r'[\W_]+', '', self.company_id.name))

    @api.multi
    def button_confirm(self):
        if any(l.exception_text for l in self.line_ids):
            raise UserError(_('This book has warnings. Fix it before confirm'))
        return super().button_confirm()

    @api.multi
    def export_xlsx(self):
        self.ensure_one()
        return self.env['report'].\
            get_action(self,
                       'l10n_es_vat_book_backported.l10n_es_vat_book_xlsx')
