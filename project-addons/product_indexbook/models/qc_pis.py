# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################
#

from openerp import models, fields, api
from time import strftime
from lxml import etree


class qc_pis_aspects(models.Model):
    _name = 'qc.pis.aspects'
    _description = 'Aspect'

    name = fields.Many2one(string='Parameter', comodel_name='qc.aspects', ondelete='restrict', readonly=True)
    remark = fields.Char(string='Remark')
    compliant = fields.Boolean(string="Compliant", default=False)
    non_compliant = fields.Boolean(string="Non compliant", default=False)
    pis = fields.Many2one(string='Product identification sheet', comodel_name='qc.pis', ondelete='cascade')

    @api.onchange('compliant')
    def _check_compliant(self):
        if self.compliant:
            self.non_compliant = False

    @api.onchange('non_compliant')
    def _check_non_compliant(self):
        if self.non_compliant:
            self.compliant = False


class qc_pis_micro_chars_details(models.Model):
    _name = 'qc.pis.micro.chars.details'
    _order = 'name'

    name = fields.Many2one(string='Micro character', comodel_name='qc.micro.chars', ondelete='restrict', readonly=True)
    parent = fields.Many2one(comodel_name='qc.pis.micro.chars', ondelete='cascade')
    checked = fields.Many2many(comodel_name='qc.pis.micro.chars', relation='qc_pis_micro_chars_rel')


class qc_pis_micro_chars(models.Model):
    _name = 'qc.pis.micro.chars'
    _description = 'Microscopic characters'

    name = fields.Char(string='Specie', related='product_specie.name.name', readonly=True)
    idm_code_rev_var = fields.Char(string='IDM code', related='product_specie.idm_code_rev_var', readonly=True)
    product_specie = fields.Many2one(string='Product & specie relation', comodel_name='qc.species.product.template.rel', ondelete='cascade')
    micro_chars = fields.Many2many(string='Observed character', comodel_name='qc.pis.micro.chars.details', relation='qc_pis_micro_chars_rel')
    children = fields.One2many(comodel_name='qc.pis.micro.chars.details', inverse_name='parent') # For reports
    compliant = fields.Boolean(string="Compliant", default=False)
    non_compliant = fields.Boolean(string="Non compliant", default=False)
    pis = fields.Many2one(string='Product identification sheet', comodel_name='qc.pis', ondelete='cascade')

    @api.onchange('compliant')
    def _check_compliant(self):
        if self.compliant:
            self.non_compliant = False

    @api.onchange('non_compliant')
    def _check_non_compliant(self):
        if self.non_compliant:
            self.compliant = False


class qc_pis_macro_chars(models.Model):
    _name = 'qc.pis.macro.chars'
    _description = 'Macroscopic characters'

    name = fields.Char(string="Specie", related='product_specie.name.name')
    macro_char = fields.Char(string='Observed character', related='product_specie.macro', readonly=True)
    product_specie = fields.Many2one(string='Product & specie relation', comodel_name='qc.species.product.template.rel', ondelete='cascade')
    compliant = fields.Boolean(string="Compliant")
    non_compliant = fields.Boolean(string="Non compliant")
    pis = fields.Many2one(string='Product identification sheet', comodel_name='qc.pis', ondelete='cascade')

    @api.onchange('compliant')
    def _check_compliant(self):
        if self.compliant:
            self.non_compliant = False

    @api.onchange('non_compliant')
    def _check_non_compliant(self):
        if self.non_compliant:
            self.compliant = False


class qc_pis(models.Model):
    _name = 'qc.pis'
    _description = 'Product identification sheet'
    _order = 'name desc'

    name = fields.Char(string='PIS code', size=11, readonly=True, index=True)
    lot = fields.Many2one(string='Parent stock lot', comodel_name='stock.production.lot', required=False, readonly=True, index=True)
    reference = fields.Many2one(string='Reference', comodel_name='product.template', required=True, ondelete='restrict', readonly=True)
    aspect_chars = fields.One2many(string='Aspect', comodel_name='qc.pis.aspects', inverse_name='pis')
    aspect_observations = fields.Text(string='Observations')
    macro_chars = fields.One2many(string='Macroscopic characters', comodel_name='qc.pis.macro.chars', inverse_name='pis')
    macro_observations = fields.Text(string='Observations')
    micro_chars = fields.One2many(string='Microscopic characters', comodel_name='qc.pis.micro.chars', inverse_name='pis')
    micro_observations = fields.Text(string='Observations')
    completed = fields.Boolean(string='Completed analysis?', default=False)

    @api.multi
    def _create_details(self):
        # Aspect
        for aspect in self.reference.qc_aspects:
            if aspect.visible:
                self.env['qc.pis.aspects'].create({'name': aspect.id, 'pis': self.id})

        for pr_sp_rel in self.reference.qc_species:
            # Macroscopic characters
            if pr_sp_rel.macro and pr_sp_rel.macro.strip():
                self.env['qc.pis.macro.chars'].create({'product_specie': pr_sp_rel.id, 'pis': self.id})

            # Microscopic characters
            if pr_sp_rel.micro and pr_sp_rel.name.micro_characters:
                parent = self.env['qc.pis.micro.chars'].create({'product_specie': pr_sp_rel.id, 'pis': self.id})
                for character in pr_sp_rel.name.micro_characters:
                    if character.visible:
                        self.env['qc.pis.micro.chars.details'].create({'name': character.id, 'parent': parent.id})

    @api.model
    def create(self, vals):
        if not (vals.get('name') and vals['name'] == 'FIP-XX-XXXX'):
            next_code = self.env['ir.sequence'].get_id('qc.pis.pis.code', 'code')
            vals['name'] = 'FIP-' + strftime('%y') + '-' + next_code
        current = super(qc_pis, self).create(vals)
        current._create_details()
        return current

    @api.multi
    def print_pis(self):
        data = self.read([])[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'product_indexbook.report_pis',
            'datas': {
                'ids': [self.id],
                'model': 'qc.pis',
                'form': data
            },
            'name': self.name, # Set PDF filename to PIS number
            'nodestroy': True
        }

    @api.multi
    def edit_pis(self):
        ctx = self.env.context.copy()
        ctx['editing_pis'] = True
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'qc.pis',
            'res_id': self.id,
            'target': 'inline', # "inline" opens it in edit mode, but top buttons disappears (Odoo bug?)
            'context': ctx,
        }

    @api.multi
    def save_pis(self):
        ctx = self.env.context.copy()
        ctx['editing_pis'] = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'qc.pis',
            'res_id': self.id,
            'target': 'current',
            'context': ctx,
        }

    @api.model
    def new_specimen(self, product):
        # Delete previous specimen
        self.search([('name', '=', 'FIP-XX-XXXX')]).unlink()

        # Create new PIS with current product and show it
        new_id = self.create({'name': 'FIP-XX-XXXX', 'reference': product.id}).id
        view_ref = self.env['ir.model.data'].xmlid_to_res_id('product_indexbook.view_qc_pis_form')

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'qc.pis',
            'res_id': new_id,
            'view_id': view_ref,
            'target': 'current'
        }

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        context = self._context
        res = super(qc_pis, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if view_type == 'form' and context.get('active_model') == 'qc.pis' and context.get('active_id'):
            pis = self.env['qc.pis'].browse(context.get('active_id'))
            doc = etree.XML(res['arch'])

            for attribute in ['aspect', 'macro', 'micro']:
                if eval('len(pis.' + attribute + '_chars) == 0'):
                    for node in doc.xpath("/form/sheet/label[@for='" + attribute + "_observations']"):
                        node.set('style', 'display: none;')
                    for node in doc.xpath("/form/sheet/field[@name='" + attribute + "_observations']"):
                        node.set('style', 'display: none;')

            res['arch'] = etree.tostring(doc)

        return res