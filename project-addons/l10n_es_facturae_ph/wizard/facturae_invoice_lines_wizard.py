# -*- coding: utf-8 -*-
# © 2022 Pharmadus Botanicals
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields


class FacturaeInvoiceLinesWizardDetail(models.TransientModel):
    _name = 'facturae.invoice.lines.wizard.detail'

    wizard_id = fields.Many2one(
        comodel_name='facturae.invoice.lines.wizard'
    )
    invoice_line_id = fields.Integer()
    product_id = fields.Many2one(
        string='Producto',
        comodel_name='product.product',
        readonly=True
    )
    description = fields.Char(string='Descripción')
    quantity = fields.Float(string='Cantidad')
    contract_reference = fields.Char(
        string='Ref. contrato',
        help='El número de expediente de contratación'
    )
    transaction_reference = fields.Char(
        string='Ref. operación/pedido',
        help='El número de operación contable'
    )

    @api.model
    def create(self, vals):
        line_id = self.env['facturae.invoice.lines'].\
            search([('invoice_line_id', '=', vals['invoice_line_id'])])
        if line_id:
            vals['contract_reference'] = line_id.contract_reference
            vals['transaction_reference'] = line_id.transaction_reference
        return super(FacturaeInvoiceLinesWizardDetail, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(FacturaeInvoiceLinesWizardDetail, self).write(vals)
        invoice_line_ids = \
            [wizard_line_id.invoice_line_id for wizard_line_id in self]
        for invoice_line_id in invoice_line_ids:
            new_vals = vals.copy()
            new_vals['invoice_line_id'] = invoice_line_id
            self.env['facturae.invoice.lines'].create(new_vals)
        return res


class FacturaeInvoiceLinesWizard(models.TransientModel):
    _name = 'facturae.invoice.lines.wizard'

    name = fields.Char(string='Factura Nº')
    partner = fields.Char(string='Cliente')
    line_ids = fields.One2many(
        comodel_name='facturae.invoice.lines.wizard.detail',
        inverse_name='wizard_id'
    )

    @api.multi
    def save_lines(self):
        return True

    @api.multi
    def write(self, vals):
        res = super(FacturaeInvoiceLinesWizard, self).write(vals)

        # Borramos los que se quedan sin datos que guardar
        invoice_line_ids = []
        for line_id in self.line_ids:
            if not line_id.contract_reference and \
               not line_id.transaction_reference:
                invoice_line_ids += [line_id.invoice_line_id]
        self.env['facturae.invoice.lines']. \
            search([('invoice_line_id', 'in', invoice_line_ids)]).unlink()

        return res
