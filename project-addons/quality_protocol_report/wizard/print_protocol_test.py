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

from openerp import models, exceptions, _
from openerp.osv import fields
from openerp.addons.website.models.website import slug
from urlparse import urljoin


class PrintProtocolTest(models.TransientModel):
    """Wizard de prueba, que se lanza desde producciones y lotes,
    fuera del prototipo este wizard no debería existir, la funcionalidad de impresión debería de hacerse desde la producción en alguno de los cambios de estado,
    """
    _name = "print.protocol.test"

    def _get_print_url(self, cr, uid, ids, name, arg, context=None):
        """Genera la url de impresión, el controller la espera en este formato, pasa como parámetros la producción y el protocolo"""
        res = {}
        if context.get('relative_url'):
            base_url = '/'
        else:
            base_url = self.pool['ir.config_parameter'].\
                get_param(cr, uid, 'web.base.url')
        if context['active_model'] == u'stock.production.lot':
            obj_id = self.pool['mrp.production'].search(cr, uid, [('final_lot_id', '=', context['active_id'])])
            if not obj_id:
                return ""
            obj = self.pool['mrp.production'].browse(cr, uid, obj_id[0])
        else:
            obj = self.pool[context['active_model']].browse(cr, uid,
                                                            context['active_id'])
        for wzd in self.browse(cr, uid, ids):
            res[wzd.id] = urljoin(base_url, "protocol/print/%s/%s" % (slug(obj), slug(obj.product_id.protocol_id)))
        return res

    _columns = {
        'print_url': fields.function(_get_print_url, string="Print link",
                                     readonly=True, type="char")
    }

    def print_protocol(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids, context=context)
        # Abre vista web
        if context['active_model'] == u'stock.production.lot':
            obj_id = self.pool['mrp.production'].search(cr, uid, [('final_lot_id', '=', context['active_id'])])
            if not obj_id:
                raise exceptions.except_orm(_('Protocol error'), _('The lot not have a production'))
            obj2 = self.pool['mrp.production'].browse(cr, uid, obj_id[0])
        else:
            obj2 = self.pool[context['active_model']].browse(cr, uid,
                                                            context['active_id'])
        if not obj2.product_id.protocol_id:
            raise exceptions.except_orm(_('Protocol error'), _('The product %s not have a protocol assigned') % (obj2.product_id.name))
        return {
            'type': 'ir.actions.act_url',
            'name': "Print Protocol",
            'target': 'self',
            'url': obj.print_url,
        }
