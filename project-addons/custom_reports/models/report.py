import base64
from openerp import models
from reportlab.graphics.barcode import createBarcodeDrawing


class Report(models.Model):
    _inherit = 'report'

    def barcode(self, type, value, width=600, height=100, humanreadable=0):
        width, height, humanreadable = int(width), int(height), \
                                       bool(humanreadable)
        barcode_obj = createBarcodeDrawing(
            type, value=value, format='png', width=width, height=height,
            humanReadable = humanreadable
        )
        return base64.encodestring(barcode_obj.asString('png'))