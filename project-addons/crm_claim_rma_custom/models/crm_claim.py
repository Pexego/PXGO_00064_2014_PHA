# -*- coding: utf-8 -*-
# © 2015 Comunitea
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _
from datetime import datetime


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    date_str = fields.Date('Date without hour', compute='_get_date_str', store=True)
    doc_attached = fields.Selection((('yes', 'YES'), ('no', 'NO')), 'Attached documentation')
    sample_attached = fields.Selection((('yes', 'YES'), ('no', 'NO')), 'Sample attached')
    quality_report = fields.Text('Quality report')
    quality_control_report = fields.Boolean('Quality control')
    quality_warranty_report = fields.Boolean('Warranty report')
    tech_dir_report = fields.Text('Technical direction report')
    tech_dir_conclusion = fields.Text('Technical direction conclusion')
    result_and_solution = fields.Text('Result and solution')
    action_taken = fields.Text('Action taken')
    economic_valuation = fields.Float('Economic valuation')
    show_sections = fields.Char('Show stage', compute='_get_show_sections')
    general_dir_ver_and_auth = fields.Text('verification and authorization by general'
                                           ' management')
    products = fields.Char('Products', compute='_get_products', store=True)
    lots = fields.Char('Lots', compute='_get_lots', store=True)
    quantities = fields.Char('Quantities', compute='_get_quantities', store=True)
    picking_id = fields.Many2one('stock.picking', 'Picking',
                                 domain=[('partner_id', 'child_of', 'partner_id')])
    photo_url = fields.Char(related='picking_id.photo_url')
    production_id = fields.Many2one('mrp.production', 'Production order')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    claim_subtype = fields.Many2one('crm.claim.subtype', 'Claim subtype')
    corrective_action = fields.Boolean(default=False)
    claim_template = fields.Many2one('crm.claim.template',
                                     default=lambda rec: rec._get_default_template())
    description = fields.Text(default=lambda rec: rec._get_default_description())

    def _get_default_template(self):
        template_id = self.env['crm.claim.template'].\
            search([], limit=1, order='sequence')
        return template_id

    def _get_default_description(self):
        template_id = self._get_default_template()
        return template_id.template if template_id else ''

    @api.one
    def _get_show_sections(self):
        self.show_sections = self.stage_id.show_sections

    @api.one
    @api.depends('date')
    def _get_date_str(self):
        self.date_str = datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S').date()

    @api.one
    @api.depends('claim_line_ids.product_id')
    def _get_products(self):
        self.products = ', '.join([x.product_id.name for x in self.claim_line_ids
                                   if x.product_id])

    @api.one
    @api.depends('claim_line_ids.prodlot_id')
    def _get_lots(self):
        self.lots = ', '.join([x.prodlot_id.name for x in self.claim_line_ids if x.prodlot_id])

    @api.one
    @api.depends('claim_line_ids.product_returned_quantity')
    def _get_quantities(self):
        quantities_list = [str(x.product_returned_quantity) for x in self.claim_line_ids
                           if x.product_returned_quantity]
        self.quantities = ', '.join(quantities_list)

    @api.multi
    def onchange_partner_id(self, partner_id, email=False):
        if partner_id:
            address_id = self.env['res.partner'].search(
                [('id', '=', partner_id)])
            delivery_address_id = self.env['res.partner'].search(
                [('id', 'child_of', partner_id)])
            picking_id = self.env['stock.picking'].search(
                [
                    ('partner_id', 'child_of', partner_id),
                    ('state', '=', 'done')
                ], order='id desc', limit=1)
            return {'value': {
                'email_from': address_id.email,
                'partner_phone': address_id.phone,
                'delivery_address_id': delivery_address_id[0].id,
                'picking_id': picking_id[0].id if picking_id else False
            }}
        else:
            return {'value': {
                'email_from': False,
                'partner_phone': False,
                'delivery_address_id': False,
                'picking_id': False
            }}

    @api.model
    def create(self, vals):
        res = super(CrmClaim, self).create(vals)
        if res.picking_id:
            res.with_context({'write_direct': True, 'create_lines': True}).\
                _onchange_invoice_warehouse_type_date()
        return res

    @api.onchange('invoice_id', 'picking_id', 'warehouse_id', 'claim_type', 'date')
    def _onchange_invoice_warehouse_type_date(self):
        res = super(CrmClaim, self)._onchange_invoice_warehouse_type_date()
        claim_line_obj = self.env['claim.line']
        warehouse = self.warehouse_id
        if self.picking_id and self._context.get('create_lines', False):
            claim_lines = []
            for move in self.picking_id.move_lines:
                for packop in move.linked_move_operation_ids:
                    location_dest = claim_line_obj.get_destination_location(
                        packop.move_id.product_id, warehouse)
                    procurement = packop.move_id.procurement_id
                    warranty_return_address = claim_line_obj._warranty_return_address_values(
                        packop.move_id.product_id, self.company_id, warehouse)
                    warranty_return_address = warranty_return_address['warranty_return_partner']
                    line = {
                        'name': packop.move_id.name,
                        'claim_origin': 'none',
                        'product_id': packop.move_id.product_id.id,
                        'product_returned_quantity': packop.operation_id.product_qty,
                        'unit_sale_price': procurement.sale_line_id.price_unit,
                        'location_dest_id': location_dest.id,
                        'warranty_return_partner': warranty_return_address,
                        'prodlot_id': packop.operation_id.lot_id.id,
                        'state': 'draft',
                    }
                    claim_lines.append((0, 0, line))
            if self.env.context.get('write_direct'):
                self.write({'claim_line_ids': claim_lines})
            else:
                value = self._convert_to_cache(
                    {'claim_line_ids': claim_lines}, validate=False)
                self.update(value)
        return res

    @api.constrains('stage_id')
    def stage_id_only_create_user(self):
        claim_type_customer = \
            self.env.ref('crm_claim_type.crm_claim_type_customer')
        if self.claim_type == claim_type_customer and \
                self.create_uid and self.create_uid != self.env.user:
            raise exceptions.Warning(_('Operation not allowed'),
                                     _('Only the user who created the claim '
                                       'can change the status'))

    @api.multi
    def action_copy_template(self):
        self.description = self.claim_template.template


class CrmClaimLine(models.Model):
    _inherit = 'claim.line'

    def auto_set_warranty(self):
        return


class CrmClaimSubtype(models.Model):
    _name = 'crm.claim.subtype'

    name = fields.Char()
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda r: r.env.user.company_id)
    active = fields.Boolean(default=True)
