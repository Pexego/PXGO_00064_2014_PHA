# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_transfer_with_barcodes(self):
        errors = ''
        for item_id in self.item_ids:
            barcode = item_id.lot_barcode.strip()
            if (item_id.product_id.categ_id.lot_assignment_by_quality_dept and (
                 not item_id.lot_barcode or \
                 (item_id.lot_id.name.strip() != barcode))) and \
                    (item_id.product_id.ean13 != barcode):
                errors += item_id.lot_id.name + ': ' + \
                          item_id.product_id.name + '\n'
        if errors:
            raise exceptions.Warning('Los siguientes lotes no coinciden:\n\n' +
                                     errors)
        else:
            self.picking_id.transferred_with_barcodes = True
            self.do_detailed_transfer()


class StockTransferDetailsItems(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    lot_barcode = fields.Char()
