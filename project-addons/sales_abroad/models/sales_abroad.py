# -*- coding: utf-8 -*-
# #############################################################################
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
from openerp import models, fields, api, _, tools


class res_sales_abroad(models.Model):
    _name = 'res.sales.abroad'
    documents = fields.Char()
    country_id = fields.Many2one('res.country', ondelete='restrict')
    attachments = fields.One2many('ir.attachment', 'sales_abroad_id')

    def unlink(self, cr, uid, ids, context=None):
        # Delete all related attachments before
        attachment = self.env['ir.attachment']
        for sa in self.browse(cr, uid, ids, context=context):
            attachment.unlink(cr, uid, sa.attachments.ids, context=context)

        return super(res_sales_abroad, self).unlink(cr, uid, ids,
                                                    context=context)
