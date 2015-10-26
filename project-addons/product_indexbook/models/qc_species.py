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
from openerp.exceptions import Warning


class qc_aspects(models.Model):
    _name = 'qc.aspects'
    _description = 'Aspects'
    _order = 'id'

    name = fields.Char(string='Aspect', size=25)
    visible = fields.Boolean(string='Visible', default=True)

    _sql_constraints = [
        ('qc_aspects_name_uniq', 'unique(name)', 'This aspect already exists!'),
    ]


class qc_micro_chars(models.Model):
    _name = 'qc.micro.chars'
    _description = 'Microscopic characters'
    _order = 'name'

    name = fields.Char(string='Character')
    visible = fields.Boolean(string='Visible', default=True)

    _sql_constraints = [
        ('qc_micro_chars_name_uniq', 'unique(name)', 'This microscopic character already exists!'),
    ]

class qc_varieties(models.Model):
    _name = 'qc.varieties'
    _description = 'Specie varieties'
    _order = 'name'

    name = fields.Char(string='Variety')
    code = fields.Char(string='Short code', size=3, required=True)
    visible = fields.Boolean(string='Visible', default=True)
    specie = fields.Many2one(string='Specie', comodel_name='qc.species', ondelete='cascade')

class qc_species(models.Model):
    _name = 'qc.species'
    _description = 'Species for quality control'
    _order = 'name, idm_code_rev desc'

    name = fields.Char(string='Raw material', required=True)
    specie = fields.Char(string='Specie')
    used_part = fields.Char(string='Used part')
    idm_code = fields.Char(string='IDM code', size=8, readonly=True)
    revision = fields.Integer(string='Revision', required=True, readonly=True)
    varieties = fields.One2many(string='Specie varieties', comodel_name='qc.varieties', inverse_name='specie')
    idm_code_rev = fields.Char(string='IDM code & rev.', select=True)
    parent_revision_id = fields.Integer()
    micro_characters = fields.Many2many(string='Microscopic characters', comodel_name='qc.micro.chars')
    products = fields.One2many(string='Products', comodel_name='qc.species.product.template.rel', inverse_name='name')
    visible = fields.Boolean(string='Visible', default=True)

    def _compose_revision(self, vals):
        idm_code = vals['idm_code'] if 'idm_code' in vals else self.idm_code
        revision = str(vals['revision'] if 'revision' in vals else self.revision)
        vals['idm_code_rev'] = idm_code + '-R' + revision

    @api.model
    def create(self, vals):
        if vals.get('idm_code', False): # Is a duplicated specie from another previously existent?
            vals['parent_revision_id'] = -1
        else: # New specie, so there is no parent
            vals['idm_code'] = self.env['ir.sequence'].get_id('qc.species.idm.code', 'code')
            vals['parent_revision_id'] = 0

        if not vals.get('revision', False):
            vals['revision'] = 1

        # Search for parent and, if exists, save reference id, increase revision,
        # break parent's relation with products and hide parent
        if vals['parent_revision_id'] == -1:
            code = vals['idm_code_rev']
            parent = self.search([('idm_code_rev', '=', code)], limit=1, order='id desc')
            vals['parent_revision_id'] = parent.id
            vals['revision'] += 1
            self._compose_revision(vals) # Compose idm code & revision

            new_rev = super(qc_species, self).create(vals)

            # Change relation with varieties to the new revision, to maintain relation with products
            for item in parent.varieties:
                item.specie = new_rev.id

            # Duplicate varieties to maintaining the history
            for item in new_rev.varieties:
                parent.varieties.create({'name': item.name, 'code': item.code, 'specie': parent.id})

            # Change relation with products to the new revision
            for item in parent.products:
                item.specie = new_rev.id

            # Hide parent to prevent his use
            parent.visible = False
        else:
            self._compose_revision(vals) # Compose idm code & revision
            new_rev = super(qc_species, self).create(vals)

        return new_rev

    @api.one
    def write(self, vals):
        self._compose_revision(vals)
        return super(qc_species, self).write(vals)

    @api.multi
    def new_revision(self):
        new_rev = self.copy()
        ctx = self.env.context.copy()
        ctx['new_revision'] = True
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'qc.species',
            'res_id': new_rev.ids[0],
            'target': 'inline', # "inline" opens it in edit mode, but top buttons appears hidden (Odoo bug?)
            'context': ctx,
        }

    @api.multi
    def save_revision(self):
        ctx = self.env.context.copy()
        ctx['new_revision'] = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'qc.species',
            'res_id': self.ids[0],
            'target': 'current',
            'context': ctx,
        }


class qc_species_product_template_rel(models.Model):
    _name = 'qc.species.product.template.rel'
    _description = 'Relation between species & products'

    name = fields.Many2one(string='Raw material', comodel_name='qc.species', ondelete='restrict')
    idm_code_rev_var = fields.Char(string='IDM code', compute='_idm_code_rev_var')
    specie = fields.Char(string='Specie', related='name.specie', readonly=True)
    used_part = fields.Char(string='Used part', related='name.used_part', readonly=True)
    variety = fields.Many2one(string='Variety', comodel_name='qc.varieties', ondelete='restrict',
                              domain="[('specie', '=', name), ('visible', '=', True)]")
    macro = fields.Char(string='Macroscopic character')
    micro = fields.Boolean(string='Has micro char?', default=True)
    product = fields.Many2one(string='Product', comodel_name='product.template', ondelete='restrict')

    @api.depends('name', 'variety')
    def _idm_code_rev_var(self):
        for item in self:
            if item.variety and item.variety.code and item.variety.code.strip():
                item.idm_code_rev_var = item.name.idm_code_rev + ' (' + item.variety.code + ')'
            else:
                item.idm_code_rev_var = item.name.idm_code_rev