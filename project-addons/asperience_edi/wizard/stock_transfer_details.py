# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    def _checksum(self,sscc):
        """Devuelve el sscc pasado mas un dígito calculado"""
        iSum = 0
        for i in xrange(len(sscc)-1,-1,-2):
            iSum += int(sscc[i])
        iSum *= 3
        for i in xrange(len(sscc)-2,-1,-2):
            iSum += int(sscc[i])

        iCheckSum = (10 - (iSum % 10)) % 10

        return "%s%s" % (sscc, iCheckSum)

    @api.model
    def make_sscc(self, picking, operation, counter, type, parent=None):
        """Método con el que se calcula el sscc a partir de
        1 + aecoc + 4 digitos num albaran + secuencia 2 digitos + 1 checksum
        para escribir en el name del paquete"""
        picking_name = picking.name.split('\\')[-1][:4]
        first_num = int(picking.name.split('\\')[-1][:1])
        sequence = str(counter).zfill(2)
        if counter > 99:
            first_num += int(str(counter)[1])
            sequence = str(counter)[1:].zfill(2)
        aecoc = self.env.user.company_id.aecoc_code
        counter += 1
        sscc = str(self._checksum(str(first_num) + aecoc + picking_name + sequence ))
        op_sscc = self.env['stock.pack.operation.sscc'].create(
            {'name': sscc, 'type': type,
             'operation_ids': [(6, 0, [operation.id])], 'parent': parent})
        return counter, op_sscc

    @api.one
    def do_detailed_transfer(self):
        res = super(StockTransferDetails, self).do_detailed_transfer()
        palet = {}
        package = {}
        counter = 0
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                """
                    Crearemos 1 sscc por palet, 1 por bulto completo y
                    1 por bulto multiproducto.
                """
                if prod.packop_id.palet not in palet.keys():
                    counter, op_sscc = self.make_sscc(self.picking_id, prod.packop_id, counter, '1')
                    palet[prod.packop_id.palet] = op_sscc
                if prod.packop_id.complete:
                    parent = False
                    if prod.packop_id.palet != 0:
                        parent = palet[prod.packop_id.palet].id
                    for i in range(prod.packop_id.complete):
                        counter, op_sscc = self.make_sscc(self.picking_id, prod.packop_id, counter, '2', parent=parent)
                if prod.packop_id.package != 0:
                    if prod.packop_id.package not in package.keys():
                        parent = False
                        if prod.packop_id.palet != 0:
                            parent = palet[prod.packop_id.palet].id
                        counter, op_sscc = self.make_sscc(self.picking_id, prod.packop_id, counter, '3', parent=parent)
                        package[prod.packop_id.package] = op_sscc
                    else:
                        package[prod.packop_id.package].write({'operation_ids': [(4, prod.packop_id.id)]})
        return res
