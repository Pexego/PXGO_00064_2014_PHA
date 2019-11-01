# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from openerp.osv.expression import get_unaccent_wrapper
from datetime import datetime, date
import unicodedata
import base64


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_company = fields.Boolean('Is a Company',
            default=True,
            help="Check if the contact is a company, otherwise it is a person")
    picking_policy = fields.Selection(
            [
                ('direct', 'Deliver each product when available'),
                ('one', 'Deliver all products at once')
            ],
            'Shipping Policy',
            states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
            help="""Pick 'Deliver each product when available' if you allow partial delivery.""")
    category_id = fields.Many2many(
            comodel_name='res.partner.category',
            column1='partner_id',
            column2='category_id',
            relation='res_partner_res_partner_category_rel',
            domain=[('child_ids', '=', False)],
            string='Tags')
    display_name = fields.Char(compute='_compute_display_name', store=True)
    liens = fields.Boolean(default=False)
    insured = fields.Boolean(default=False)
    simplified_invoice = fields.Boolean(default=False)
    send_invoice_by_email = fields.Boolean(default=False)
    email_to_send_invoice = fields.Char()
    invoiced_current_year = fields.Float(digits=(16,2), compute='_total_invoiced')
    invoiced_past_year = fields.Float(digits=(16,2), compute='_total_invoiced')
    invoiced_previous_year = fields.Float(digits=(16,2), compute='_total_invoiced')
    invoiced_other_years = fields.Float(digits=(16,2), compute='_total_invoiced')
    recovery_date = fields.Date(help='Date on which the customer was recovered '
                                     'after a long period of commercial '
                                     'inactivity', readonly=True)
    it_is_an_individual = fields.Boolean(default=False)
    invoicing_period = fields.Selection([('daily', 'Daily'),
                                         ('weekly', 'Weekly'),
                                         ('monthly', 'Monthly')],
                                        default=False)

    @api.one
    @api.constrains('active')
    def _cascade_deactivation(self):
        if (not self.active) and self.child_ids:
            self.child_ids.write({'active': False})

    @api.one
    @api.constrains('invoicing_period')
    def _cascade_invoicing_period(self):
        if self.child_ids:
            self.child_ids.write({'invoicing_period': self.invoicing_period})

    @api.one
    @api.constrains('parent_id')
    def _parent_invoicing_period(self):
        if self.parent_id:
            self.invoicing_period = self.parent_id.invoicing_period

    @api.onchange('sii_simplified_invoice')
    def _sii_simplified_invoice_change(self):
        self.simplified_invoice = self.sii_simplified_invoice

    @api.one
    def _total_invoiced(self):
        this_year = datetime.now().year
        invoices_domain = [
            ('partner_id', '=', self.id),
            ('type', 'ilike', 'out_%'),
            ('state', 'in', ('open', 'paid'))
        ]

        date_begin = fields.Date.to_string(date(this_year, 1, 1))
        date_end = fields.Date.to_string(date(this_year, 12, 31))
        current_year_invoices = self.invoice_ids.search(
            invoices_domain +
            [('date_invoice', '>=', date_begin),
             ('date_invoice', '<=', date_end)]
        )

        date_begin = fields.Date.to_string(date(this_year - 1, 1, 1))
        date_end = fields.Date.to_string(date(this_year - 1, 12, 31))
        past_year_invoices = self.invoice_ids.search(
            invoices_domain +
            [('date_invoice', '>=', date_begin),
             ('date_invoice', '<=', date_end)]
        )

        date_begin = fields.Date.to_string(date(this_year - 2, 1, 1))
        date_end = fields.Date.to_string(date(this_year - 2, 12, 31))
        previous_year_invoices = self.invoice_ids.search(
            invoices_domain +
            [('date_invoice', '>=', date_begin),
             ('date_invoice', '<=', date_end)]
        )

        date_limit = fields.Date.to_string(date(this_year - 2, 1, 1))
        other_years_invoices = self.invoice_ids.search(
            invoices_domain + [('date_invoice', '<', date_limit)]
        )

        self.invoiced_current_year = sum(current_year_invoices.mapped(
            lambda r: r.amount_untaxed if r.type == 'out_invoice'
                                     else -r.amount_untaxed))
        self.invoiced_past_year =  sum(past_year_invoices.mapped(
            lambda r: r.amount_untaxed if r.type == 'out_invoice'
                                     else -r.amount_untaxed))
        self.invoiced_previous_year = sum(previous_year_invoices.mapped(
            lambda r: r.amount_untaxed if r.type == 'out_invoice'
                                     else -r.amount_untaxed))
        self.invoiced_other_years = sum(other_years_invoices.mapped(
            lambda r: r.amount_untaxed if r.type == 'out_invoice'
                                     else -r.amount_untaxed))

    @api.one
    @api.depends('name', 'parent_id', 'parent_id.name')
    def _compute_display_name(self):
        if self.parent_id:
            self.display_name = self.parent_id.name + ', ' + self.name
        else:
            self.display_name = self.name

    @api.model
    def create(self, vals):
        if vals.get('parent_id', False) != False:
            vals['is_company'] = False
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        if self.env.context.get('partner_special_form', False)\
                and (len(self.ids) == 1):
            sql = """update res_partner set vat = '{vat}' where id = {id};"""\
                .format(id = self.id, vat = vals['vat'])
            self.env.cr.execute(sql)
            return True
        else:
            return super(ResPartner, self).write(vals)

    @api.multi
    def name_get(self):
        key = 'concatenate_name_comercial'

        # If key is defined and form is in create mode
        if key in self._context and self._context.get(key):
            res = []
            for rec in self:
                name = rec.name + \
                       (' (' + rec.comercial + ')' if rec.comercial else '')
                res.append((rec.id, name))
            return res
        else:
            return super(ResPartner, self).name_get()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            self.check_access_rights('read')
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            query = """SELECT id
                         FROM res_partner
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent}
                           OR {comercial} {operator} {percent})
                     ORDER BY {display_name}
                    """.format(where=where_str, operator=operator,
                               email=unaccent('email'),
                               display_name=unaccent('display_name'),
                               comercial=unaccent('comercial'),
                               percent=unaccent('%s'))

            where_clause_params += [search_name, search_name, search_name]
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            ids = map(lambda x: x[0], self.env.cr.fetchall())

            if ids:
                return self.browse(ids).name_get()
            else:
                return []
        return super(ResPartner,self).name_search(name, args, operator=operator, limit=limit)

    @api.multi
    def view_supplier_products(self):
        request_id = self.env['purchasable.products']._get_products(self)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'purchasable.products',
            'domain': [('request_id', '=', request_id)],
            'target': 'current',
            'context': self.env.context,
        }

    @api.multi
    def run_action_find_recovered_customers(self):
        self.env.ref('custom_views.action_find_recovered_customers').run()

    @api.multi
    def generate_email_csv(self):
        csv = u'NOMBRE,EMAIL\n'
        for partner in self.filtered(lambda r: r.email and r.email > ''):
            name = partner.name if partner.name else ''
            csv += u'{},{}\n'.format(name.replace(',', ' '),
                                     partner.email.replace(',', ' '))

        csv = unicodedata.normalize('NFKD', csv).encode('ascii', 'ignore')
        csv = base64.encodestring(csv)
        filename = 'odoo_emails.csv'

        ir_attachment = self.env['ir.attachment']
        attachment = ir_attachment.search([('res_model', '=', self._name),
                                           ('res_id', '=', 0),
                                           ('name', '=', filename)])
        if attachment:
            attachment.write({'datas': csv})
        else:
            attachment = ir_attachment.create({
                'name': filename,
                'datas': csv,
                'datas_fname': filename,
                'res_model': self._name,
                'res_id': 0,
                'type': 'binary'
            })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/saveas?model=ir.attachment&field=datas' +
                   '&filename_field=name&id=%s' % (attachment.id),
            'target': 'self',
        }