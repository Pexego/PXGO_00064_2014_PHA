try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from PIL import Image

from openerp import models


class Report(models.Model):
    _inherit = 'report'

    def barcode_base64(self, type, value, width=600, height=100,
                       humanreadable=0, rotate=0):
        image_str = self.barcode(type, value, width, height, humanreadable)

        if rotate == 0:
            return image_str.encode('base64')
        else:
            image_stream = StringIO.StringIO(image_str)
            orig_img = Image.open(image_stream)

            img = Image.new('RGB', (height, width), 'white')
            img.paste(orig_img.rotate(rotate, Image.NEAREST, True), (0,0))

            background_stream = StringIO.StringIO()
            img.save(background_stream, orig_img.format.upper())
            return background_stream.getvalue().encode('base64')