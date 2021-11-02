from openerp import models, api, exceptions, _


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    @api.model
    def view_init(self, fields_list):
        warning_messages = ''
        for picking_id in self.env['stock.picking'].\
            browse(self.env.context.get('active_ids')):
            partner_id = picking_id.partner_id.parent_id \
                if picking_id.partner_id.parent_id else picking_id.partner_id
            if picking_id.company_id.country_id.code == 'ES' and \
                    not partner_id.vat and \
                    not (partner_id.simplified_invoice and
                         partner_id.sii_simplified_invoice):
                warning_messages += '[{}] {}\n'.format(picking_id.name,
                                                       partner_id.name)
        if warning_messages:
            raise exceptions.Warning(_('Cannot continue due to pickings with '
                                       'customers without VAT number and '
                                       'without simplified invoice marking:\n'),
                                     warning_messages)
        return super(StockInvoiceOnshipping, self).view_init(fields_list)
