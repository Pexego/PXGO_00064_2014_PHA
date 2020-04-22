# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _get_partner_access_link(self, cr, uid, mail, partner=None,
                                 context=None):
        # Desactivamos el mensaje al pie de la compañía, para evitar enlace
        # al portal y demás florituras no deseadas...
        return ''