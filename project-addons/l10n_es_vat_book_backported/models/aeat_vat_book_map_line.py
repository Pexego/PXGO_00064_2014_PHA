# -*- coding: utf-8 -*-
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import fields, models, api


class AeatVatBookMapLines(models.Model):
    _name = 'aeat.vat.book.map.line'
    _description = 'AEAT Vat Book Map Line'

    def _selection_special_tax_group(self):
        return self.env['l10n.es.vat.book.line.tax'].fields_get(
            allfields=['special_tax_group'])['special_tax_group']['selection']

    name = fields.Char(
        string='Name',
    )
    book_type = fields.Selection(
        selection=[
            ('issued', 'Issued'),
            ('received', 'Received'),
        ],
        string='Book type',
    )
    special_tax_group = fields.Selection(
        selection=_selection_special_tax_group,
        string='Special group',
        help='Special tax group as R.Eq, IRPF, etc',
    )
    fee_type_xlsx_column = fields.Char(
        string='Type xlsx column'
    )
    fee_amount_xlsx_column = fields.Char(
        string='Base xlsx column'
    )
    tax_tmpl_ids = fields.Many2many(
        comodel_name='account.tax.template',
        string="Taxes",
    )

    @api.multi
    def map_tax_template(self, tax_template, company_id):
        """Adds a tax template -> tax id to the mapping.
        Adapted from account_chart_update module.

        :param self: Single invoice record.
        :param tax_template: Tax template record.
        :return: Tax template current mapping
        """
        self.ensure_one()
        if not tax_template:
            return self.env['account.tax']
        # search inactive taxes too, to avoid re-creating
        # taxes that have been deactivated before
        tax_obj = self.env['account.tax'].with_context(active_test=False)
        criteria = ['|',
                    ('name', '=', tax_template.name),
                    ('description', '=', tax_template.name)]
        if tax_template.description:
            criteria = ['|'] + criteria
            criteria += [
                '|',
                ('description', '=', tax_template.description),
                ('name', '=', tax_template.description),
            ]
        criteria += [('company_id', '=', company_id.id)]
        return tax_obj.search(criteria)

    @api.multi
    def _get_vat_book_taxes_map(self, company_id):
        self.ensure_one()
        taxes = self.env['account.tax']
        for tax_template in self.tax_tmpl_ids:
            taxes |= self.map_tax_template(tax_template, company_id)
        return taxes

    def get_invoice_lines(self, report):
        invoice_lines = self.env['account.invoice.line'].\
            search([('invoice_id.period_id', 'in', report.periods.ids),
                    ('invoice_id.move_id', '!=', False),
                    '|', ('invoice_line_tax_id', 'in',
                     self._get_vat_book_taxes_map(report.company_id).ids),
                     ('invoice_line_tax_id.child_ids', 'in',
                     self._get_vat_book_taxes_map(report.company_id).ids)])
        return invoice_lines


class ResPartner(models.Model):
    _inherit = "res.partner"

    aeat_anonymous_cash_customer = fields.Boolean(
        string='AEAT - Anonymous customer',
        help='Check this for anonymous cash customer. AEAT communication',
    )

    @api.multi
    def _map_aeat_country_code(self, country_code):
        country_code_map = {
            'RE': 'FR',
            'GP': 'FR',
            'MQ': 'FR',
            'GF': 'FR',
            'EL': 'GR',
        }
        return country_code_map.get(country_code, country_code)

    @api.multi
    def _get_aeat_europe_codes(self):
        europe = self.env.ref('base.europe', raise_if_not_found=False)
        if not europe:
            europe = self.env["res.country.group"].search(
                [('name', '=', 'Europe')], limit=1)
        return europe.country_ids.mapped('code')

    @api.multi
    def _parse_aeat_vat_info(self):
        """ Return tuple with split info (country_code, identifier_type and
            vat_number) from vat and country partner
        """
        self.ensure_one()
        vat_number = self.vat or ''
        prefix = self._map_aeat_country_code(vat_number[:2].upper())
        if prefix in self._get_aeat_europe_codes():
            country_code = prefix
            vat_number = vat_number[2:]
            identifier_type = '02'
        else:
            country_code = self._map_aeat_country_code(
                self.country_id.code) or ''
            if country_code in self._get_aeat_europe_codes():
                identifier_type = '02'
            else:
                identifier_type = '04'
        if country_code == 'ES':
            identifier_type = ''
        return country_code, identifier_type, vat_number
