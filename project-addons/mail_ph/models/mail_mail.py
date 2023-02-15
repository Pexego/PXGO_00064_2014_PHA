# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api
import urllib3, base64


class MailMail(models.Model):
    _inherit = 'mail.mail'

    class MailMail(models.Model):
        _inherit = 'mail.mail'

        def _get_partner_access_link(self, cr, uid, mail, partner=None,
                                     context=None):
            # Desactivamos el mensaje al pie de la compañía, para evitar enlace
            # al portal y demás florituras no deseadas...
            return ''

    @api.model
    def create(self, vals):
        res = super(MailMail, self).create(vals)
        # Detect if the user is trying to send a fax
        if res.subject and '4955 - EO' in res.subject:
            res.send_to_web2fax()
        return res

    def send_to_web2fax(self):
        # Inform our web2fax service to watch fax sending result
        if self.attachment_ids:
            attachment = self.attachment_ids[0]
            fields = {
                'iEnviar': '1',
                'fax': self.email_to.split('@')[0],  # Fax number
                'email_aviso': self.env.user.login,
                'adjunto': (attachment.datas_fname,
                            base64.b64decode(attachment.datas)),
            }
            url = 'http://cloud.pharmadus.com/extranet/web2fax/submit.php'
            http = urllib3.PoolManager()
            headers = urllib3.util.make_headers(basic_auth='ph:ph')
            r = http.request_encode_body('POST', url, fields=fields,
                                         headers=headers, encode_multipart=True)
            if 'El envío se ha realizado correctamente.' in r.data:
                self.state = 'sent'
            else:
                self.state = 'exception'
        else:
            self.state = 'cancel'
