# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api
import urllib3


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
        if '4955 - EO' in res.subject:
            res.notify_web2fax()
        return res

    def notify_web2fax(self):
        # Inform our web2fax service to watch fax sending result
        link = 'http://cloud.pharmadus.com/extranet/web2fax/' \
               'vigilar_odoo.php?fax={}&email={}&id={}'.format(
            self.email_to.split('@')[0],  # Fax number
            self.env.user.login,
            self.subject.split(' - ')[1]  # Message ID
        )
        http = urllib3.PoolManager()
        headers = urllib3.util.make_headers(basic_auth='ph:ph')
        http.request('GET', link, headers=headers)