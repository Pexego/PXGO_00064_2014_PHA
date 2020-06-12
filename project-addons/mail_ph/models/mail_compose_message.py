# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def generate_email_for_composer_batch(self, cr, uid, template_id, res_ids, context=None, fields=None):
        """ Call email_template.generate_email(), get fields relevant for
            mail.compose.message, transform email_cc and email_to into partner_ids """
        if context is None:
            context = {}
        if fields is None:
            fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc',  'reply_to', 'attachment_ids', 'mail_server_id']
        returned_fields = fields + ['partner_ids', 'attachments']
        values = dict.fromkeys(res_ids, False)

        ctx = dict(context, tpl_partners_only=not context.get('tpl_partners_only_disabled', False))

        template_values = self.pool.get('email.template').generate_email_batch(cr, uid, template_id, res_ids, fields=fields, context=ctx)
        for res_id in res_ids:
            res_id_values = dict((field, template_values[res_id][field]) for field in returned_fields if template_values[res_id].get(field))
            res_id_values['body'] = res_id_values.pop('body_html', '')
            values[res_id] = res_id_values
        return values
