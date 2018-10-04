# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
import time


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    complete = fields.Integer('Number of complete',
                              compute='_compute_packages_and_weight',
                              readonly=True,
                              store=True)
    number_of_packages = fields.Integer('Number of packages',
                              required=True,
                              default=0)
    number_of_palets = fields.Integer('Number of palets',
                              compute='_compute_packages_and_weight',
                              readonly=True,
                              store=True)
    real_weight = fields.Float('Real weight to send',
                              required=True,
                              default=0)
    expedition_id = fields.Many2one('stock.expeditions',
                              'Associated expedition')
    carrier_note = fields.Text(related='sale_id.carrier_note')

    @api.one
    @api.depends('pack_operation_ids',
                 'pack_operation_ids.complete',
                 'pack_operation_ids.package',
                 'pack_operation_ids.product_qty',
                 'pack_operation_ids.product_id')
    def _compute_packages_and_weight(self):
        if len(self.pack_operation_ids) > 0:
            complete_sum = 0
            weight_sum = 0
            package_list = [] # Count different packages
            palet_list = []   # Count different palets

            for po in self.pack_operation_ids:
                complete_sum += po.complete
                if po.package > 0 and not po.package in package_list:
                    package_list.append(po.package)
                if po.palet > 0 and not po.palet in palet_list:
                    palet_list.append(po.palet)
                weight_sum += po.product_id.product_tmpl_id.weight * po.product_qty

            self.complete = complete_sum
            self.number_of_palets = len(palet_list)
            self.weight = weight_sum

    @api.one
    def create_expedition(self):
        if self.state == 'done' and self.picking_type_id.code == 'outgoing':
            expeditions = self.env['stock.expeditions']
            if not expeditions.search([('picking_id', '=', self.id)]):
                self.expedition_id = expeditions.create({'picking_id': self.id})

    @api.multi
    def do_print_picking(self):
        # Redirects to the new report
        return self.env['report'].\
            get_action(self, 'warehouse_shipping_light.wsl_report_picking')

    def _prepare_shipping_invoice_line(self, cr, uid, picking, invoice, context):
        # First, check if the carrier is the same in picking as in sale order
        if picking.sale_id:
            for line in picking.sale_id.order_line:
                if line.is_delivery and \
                         line.product_id != picking.carrier_id.product_id:
                    # Replace old carrier product with the new one at sale and
                    # invoice orders lines
                    for invline in invoice.invoice_line:
                        if invline.product_id == line.product_id:
                            invline.product_id = picking.carrier_id.product_id
                            invline.name = invline.product_id.name
                    line.product_id = picking.carrier_id.product_id
                    line.name = line.product_id.name

        # Create shipping invoice line with the same price/qty of origin
        res = super(StockPicking, self)._prepare_shipping_invoice_line(cr, uid,
                                                      picking, invoice, context)
        if res and picking.sale_id:
            for line in picking.sale_id.order_line:
                if line.is_delivery:
                    # Maintain original sale order price & quantity
                    res['price_unit'] = line.price_unit
                    res['quantity'] = line.product_uom_qty
        return res

    @api.multi
    def write(self, vals):
        carrier_id = vals.get('carrier_id', False)
        if carrier_id:
            old_carriers = {}
            for p in self:
                old_carriers[p.id] = p.carrier_id

        res = super(StockPicking, self).write(vals)

        if carrier_id:
            for rec in self:
                if rec.sale_id and rec.sale_id.carrier_id != carrier_id:
                    rec.sale_id.carrier_id = carrier_id
                    for line in rec.sale_id.order_line:
                        if line.is_delivery and \
                               line.product_id != rec.carrier_id.product_id:
                            line.product_id = rec.carrier_id.product_id
                            line.name = line.product_id.name

                if rec.expedition_id and old_carriers[rec.id] != carrier_id:
                    rec.expedition_id._compute_carrier_name()
        return res


class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'
    _order = 'product_id, id'

    palet = fields.Integer('Palet', default=0)
    complete = fields.Integer('Complete')
    package = fields.Integer('Package', default=0)
    rest = fields.Float('Rest', default=0)
    transfer_detail_item = fields.Integer(default=0)

    @api.model
    def create(self, vals):
        vals['rest'] = vals.get('quantity', 0)

        td = self.env['stock.transfer_details'].search(
            [('picking_id', '=', vals['picking_id'])],
            order='id desc')
        if td:
            td = td[0]
            tdi = False
            po_ids = self.search([('picking_id', '=', td.picking_id.id),
                                  ('transfer_detail_item', '>', 0)])
            assigned_tdi_ids = [po.transfer_detail_item for po in po_ids]
            for item in td.item_ids:
                if (item.product_id.id == vals['product_id'] and
                   item.lot_id.id == vals['lot_id'] and
                   item.quantity == vals['product_qty'] and
                   item.sourceloc_id.id == vals['location_id'] and
                   item.destinationloc_id.id == vals['location_dest_id'] and
                   item.id not in assigned_tdi_ids):
                    tdi = item

        if td and tdi:
            vals['palet'] = tdi.palet
            vals['complete'] = tdi.complete
            vals['package'] = tdi.package
            vals['rest'] = tdi.rest
            vals['transfer_detail_item'] = tdi.id

        return super(StockPackOperation, self).create(vals)


class StockExpeditions(models.Model):
    _name = 'stock.expeditions'
    _inherits = {'stock.picking': 'picking_id'}
    _description = 'Expeditions'

    picking_id = fields.Many2one(
        'stock.picking',
        'Picking',
        required=True,
        ondelete='cascade')
    date_done_day = fields.Char('Day',
                              compute='_compute_day_done',
                              store=True)
    date_done_hour = fields.Char('Hour',
                              compute='_compute_day_done',
                              store=True)
    carrier_partner_name = fields.Char('Carrier',
                              compute='_compute_carrier_name',
                              store=True)
    carrier_sale_line = fields.Many2one(
                              'sale.order.line',
                              store=True)
    zip = fields.Char(related='move_lines.partner_id.zip',
                      readonly=True)
    city = fields.Char(related='move_lines.partner_id.city',
                       readonly=True)
    state_id = fields.Many2one(related='move_lines.partner_id.state_id',
                               readonly=True)
    country_id = fields.Many2one(related='move_lines.partner_id.country_id',
                                 readonly=True)
    sent = fields.Integer('Sent', default=0)
    amount_gross_untaxed = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    article_discount = fields.Float(
        'Article discount',
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    amount_with_article_discount = fields.Float(
        'Amount with article discount',
        compute='_compute_amount',
        store=True,
        readonly=True)
    amount_net_untaxed = fields.Float(
        'Net amount',
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    commercial_discount_display = fields.Char(
        size = 32,
        compute='_compute_amount',
        store=True,
        readonly=True)
    commercial_discount_amount = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    financial_discount_display = fields.Char(
        size=32,
        compute='_compute_amount',
        store=True,
        readonly=True)
    financial_discount_amount = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    amount_untaxed = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    amount_tax = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    amount_total = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)

    @api.model
    def create(self, vals):
        p = self.env['stock.picking'].browse(vals['picking_id'])

        if p.sale_id:
            # Search for carrier charge in sale order lines
            for sale_line in p.sale_id.order_line:
                if sale_line.is_delivery:
                    vals['carrier_sale_line'] = sale_line.id

            # If not exists carrier sale line
            if not vals.get('carrier_sale_line', False):
                original_state = p.sale_id.state
                p.sale_id.state = 'draft'
                p.sale_id.carrier_id = p.carrier_id
                p.sale_id.delivery_set()
                p.sale_id.state = original_state
                for sale_line in p.sale_id.order_line:
                    if sale_line.is_delivery:
                        sale_line.state = 'confirmed'
                        vals['carrier_sale_line'] = sale_line.id

        return super(StockExpeditions, self).create(vals)

    @api.one
    @api.depends('carrier_id',
                 'carrier_id.partner_id')
    def _compute_carrier_name(self):
        name = self.carrier_id.partner_id.comercial
        if name:
            name = name + ' - ' + self.carrier_id.partner_id.name
        else:
            name = self.carrier_id.partner_id.name
        self.carrier_partner_name = name

    @api.one
    @api.depends('date_done')
    def _compute_day_done(self):
        day = self.date_done if self.date_done else self.date
        self.date_done_day = time.strftime('%Y/%m, día %d',
                                        time.strptime(day, '%Y-%m-%d %H:%M:%S'))
        self.date_done_hour = time.strftime('%H:%M:%S',
                                        time.strptime(day, '%Y-%m-%d %H:%M:%S'))

    @api.one
    @api.depends('carrier_sale_line')
    def _compute_amount(self):
        amount_gross = 0
        art_disc_amount = 0
        com_discount = 0
        com_disc_amount = 0
        com_discount_global = 0
        fin_discount = 0
        fin_disc_amount = 0
        fin_discount_global = 0
        amount_tax = 0

        for line in self.move_lines:
            sale_line = line.procurement_id.sale_line_id
            amount = line.product_qty * sale_line.price_unit
            amount_gross += amount
            art_disc_amount += amount * sale_line.discount / 100
            aux = amount * (1 - sale_line.discount / 100)
            com_discount = sale_line.commercial_discount
            com_disc_amount += aux * com_discount / 100
            aux = aux * (1 - com_discount / 100)
            fin_discount = sale_line.financial_discount
            fin_disc_amount += aux * fin_discount / 100
            aux = aux * (1 - fin_discount / 100)
            com_discount_global = com_discount or com_discount_global
            fin_discount_global = fin_discount or fin_discount_global
            # Compute line taxes
            for c in sale_line.tax_id.compute_all(aux, 1, line.product_id,
                                      self.sale_id.partner_id)['taxes']:
                amount_tax += c.get('amount', 0.0)

        # Amounts from carrier charge
        sale_line = self.carrier_sale_line
        amount = sale_line.product_uom_qty * sale_line.price_unit
        amount_gross += amount
        art_disc_amount += amount * sale_line.discount / 100
        aux = amount * (1 - sale_line.discount / 100)
        com_discount = sale_line.commercial_discount
        com_disc_amount += aux * com_discount / 100
        aux = aux * (1 - com_discount / 100)
        fin_discount = sale_line.financial_discount
        fin_disc_amount += aux * fin_discount / 100
        aux = aux * (1 - fin_discount / 100)
        # Compute sale line taxes
        for c in sale_line.tax_id.compute_all(aux, 1, sale_line.product_id,
                                  self.sale_id.partner_id)['taxes']:
            amount_tax += c.get('amount', 0.0)

        # Save calculated totals
        self.amount_gross_untaxed = amount_gross
        self.article_discount = art_disc_amount
        self.amount_with_article_discount = amount_gross - art_disc_amount
        self.commercial_discount_amount = com_disc_amount
        self.amount_net_untaxed = amount_gross - art_disc_amount - \
                                  com_disc_amount
        self.financial_discount_amount = fin_disc_amount
        self.amount_untaxed = self.amount_net_untaxed - fin_disc_amount
        self.amount_tax = amount_tax
        self.amount_total = self.amount_untaxed + self.amount_tax

        if com_discount_global > 0:
            self.commercial_discount_display = \
                _('Commercial discount (%.2f %%)') % com_discount_global
        else:
            self.commercial_discount_display = _('Commercial discount')

        if fin_discount_global > 0:
            self.financial_discount_display = \
                _('Financial discount (%.2f %%)') % fin_discount_global
        else:
            self.financial_discount_display = _('Financial discount')


class StockLocation(models.Model):
    _inherit = 'stock.location'

    sscc_digit = fields.Char('SSCC Digit', size=1)
