# -*- coding: utf-8 -*-
# © 2022 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api, _


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    def write(self, vals):
        disable_notify_changes = self.env.context.get('disable_notify_changes',
                                                      False)
        if not disable_notify_changes:
            orig_values = {}
            attrs = self.fields_get()
            for mrp_bom in self:
                orig_values[mrp_bom.id] = {}
                for field in vals:
                    field_value = eval('mrp_bom.' + field)
                    field_type = attrs[field]['type']
                    if field == 'bom_line_ids':
                        orig_values[mrp_bom.id][field] = u"<br/>" + u"<br/> ".join(
                            [x.display_name + ' => ' + str(x.product_qty)
                             for x in field_value]
                        ) + u"<br/>"
                    elif field_type in ['one2many', 'many2one', 'many2many']:
                        orig_values[mrp_bom.id][field] = u", ".join(
                            [x.display_name for x in field_value]
                        )
                    else:
                        orig_values[mrp_bom.id][field] = field_value

        res = super(MrpBom, self).write(vals)

        if disable_notify_changes:
            return res

        for mrp_bom in self:
            fields = ''
            for field in vals:
                field_value = eval('mrp_bom.' + field)
                field_type = attrs[field]['type']
                if field == 'bom_line_ids':
                    new_value = u"<br/> " + u"<br/> ".join(
                        [x.display_name + ' => ' + str(x.product_qty)
                         for x in field_value]
                    )
                elif field_type == 'binary':
                    new_value = _('(new binary data)') if field_value else False
                elif field_type in ['one2many', 'many2one', 'many2many']:
                    new_value = u", ".join(
                        [x.display_name for x in field_value]
                    )
                else:
                    new_value = field_value

                if field_type == 'binary':
                    orig_value = _('(old binary data)') if \
                        orig_values[mrp_bom.id][field] else False
                else:
                    orig_value = orig_values[mrp_bom.id][field]

                orig_value = orig_value if orig_value else _('(no data)')
                new_value = new_value if new_value else _('(no data)')
                fields += u'<br/><br/>{0}: {1} >> {2}'.format(
                        _(attrs[field]['string']), orig_value, new_value)

            mrp_bom.message_post(body=_('Modified fields: ') + fields)

        return res
