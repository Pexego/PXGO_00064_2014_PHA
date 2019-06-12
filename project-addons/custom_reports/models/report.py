try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from PIL import Image
from reportlab.graphics.barcode import createBarcodeDrawing
import io
import code128

from openerp import models


class Report(models.Model):
    _inherit = 'report'

    def barcode_format(self, barcode_type, value, width=600, height=100,
                       humanreadable=0, format='png'):
        if barcode_type == 'UPCA' and len(value) in (11, 12, 13):
            barcode_type = 'EAN13'
            if len(value) in (11, 12):
                value = '0%s' % value
        try:
            if barcode_type == 'Code128_CleanLines':
                barcode = code128.code128_image(data=value)
                with io.BytesIO() as output:
                    barcode.save(output, format=format)
                    contents = output.getvalue()
                return contents
            else:
                humanreadable = bool(humanreadable)
                barcode = createBarcodeDrawing(
                    barcode_type, value=value, format=format, width=width,
                    height=height, humanReadable=humanreadable
                )
                return barcode.asString(format)
        except (ValueError, AttributeError):
            raise ValueError("Cannot convert into barcode.")

    def barcode_base64(self, type, value, width=600, height=100,
                       humanreadable=0, rotate=0):
        image_str = self.barcode_format(type, value, width, height,
                                        humanreadable, 'png')
        if rotate == 0:
            return image_str.encode('base64')
        else:
            image_stream = StringIO.StringIO(image_str)
            orig_img = Image.open(image_stream)

            img = Image.new('RGB', (height, width), 'white')
            img.paste(orig_img.rotate(rotate, Image.NEAREST, True), (0, 0))

            background_stream = StringIO.StringIO()
            img.save(background_stream, orig_img.format.upper())
            return background_stream.getvalue().encode('base64')
