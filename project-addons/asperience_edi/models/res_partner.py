# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
#
##############################################################################
from openerp import models, fields

class ResPartnerCustomEdi(models.Model):

    _name = 'res.partner.custom.edi'

    partner_id = fields.Many2one('res.partner', 'Partner')
    document = fields.Selection((('desadv', 'DESADV'), ('invoic', 'INVOIC')))
    section = fields.Char()
    action = fields.Selection((('remove', 'Remove'), ('edit', 'Edit')))
    search_value = fields.Char()
    set_value = fields.Char()


class ResPartner(models.Model):

    _inherit = "res.partner"

    gln = fields.Char("GLN")
    edi_supplier_ref = fields.Char("Supplier EDI")
    edi_partner = fields.Char("Partner EDI")
    edi_desadv = fields.Boolean("EDI DESADV")
    custom_edi = fields.One2many('res.partner.custom.edi', 'partner_id')
    use_date_as_life_date = fields.Boolean()
    edi_mercantil = fields.Char(compute='_compute_edi_mercantil')

    def _compute_edi_mercantil(self):
        for partner in self:
            edi_mercantil = ''
            if partner.es_registro_mercantil:
                edi_mercantil += 'RM %s ' % partner.es_registro_mercantil
            if partner.es_tomo:
                edi_mercantil += 'T %s ' % partner.es_tomo
            if partner.es_libro:
                edi_mercantil += 'L %s ' % partner.es_libro
            if partner.es_folio:
                edi_mercantil += 'F %s ' % partner.es_folio
            if partner.es_seccion:
                edi_mercantil += 'S %s ' % partner.es_seccion
            if partner.es_hoja:
                edi_mercantil += 'H %s ' % partner.es_hoja
            partner.edi_mercantil = edi_mercantil

