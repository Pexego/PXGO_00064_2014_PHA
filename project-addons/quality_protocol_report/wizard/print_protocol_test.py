# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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

from openerp import models
from openerp.osv import fields
from openerp.addons.website.models.website import slug
from urlparse import urljoin


class PrintProtocolTest(models.TransientModel):

    _name = "print.protocol.test"

    def _get_print_url(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if context.get('relative_url'):
            base_url = '/'
        else:
            base_url = self.pool['ir.config_parameter'].\
                get_param(cr, uid, 'web.base.url')
        obj = self.pool[context['active_model']].browse(cr, uid,
                                                        context['active_id'])
        for wzd in self.browse(cr, uid, ids):
            res[wzd.id] = urljoin(base_url, "protocol/print/%s/%s" % (slug(obj), slug(wzd.protocol_id)))
        return res

    _columns = {
        'protocol_id': fields.many2one("quality.protocol.report",
                                       "Protocol", required=True),
        'print_url': fields.function(_get_print_url, string="Print link",
                                     readonly=True, type="char")
    }

    def print_protocol(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids, context=context)
        return {
            'type': 'ir.actions.act_url',
            'name': "Print Protocol",
            'target': 'self',
            'url': obj.print_url,
        }
