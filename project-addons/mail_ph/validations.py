# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

# mail_re = "^.+\\@(\\[?)[a-zA-Z0-9\\-\\_\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$"
mail_re = "^.+\\@(\\[?)[a-zA-Z0-9\\-\\_\\.]+\\.[a-zA-Z0-9]+(\\]?)$"
fax_re = "^\d{9,}$"

def is_valid_email(email):
    if email:
        is_ok = True
        for m in email.split(','):
            res = re.match(mail_re, m)
            is_ok = is_ok and res and res.group() == m
        return is_ok
    else:
        return False

def is_valid_fax(fax):
    if fax:
        fax = fax.replace(' ', '')
        if fax[0:3] == '+34':
            fax = fax[3:]
        elif fax[0:4] == '0034':
            fax = fax[4:]
        res = re.match(fax_re, fax)
        return res and res.group() == fax
    else:
        return False