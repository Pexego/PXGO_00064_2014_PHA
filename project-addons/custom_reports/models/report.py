import base64
from openerp import models


class Report(models.Model):
    _inherit = 'report'

    def barcode_base64(self, type, value, width=600, height=100,
                       humanreadable=0):
        return base64.encodestring(self.barcode(type, value, width, height,
                                                humanreadable))