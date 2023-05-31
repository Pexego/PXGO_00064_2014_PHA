# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    copy_analysis_from = fields.Many2one(string='Copy from...',
                                         comodel_name='product.product')
    copy_data_from = fields.Many2one(string='Copy data from...',
                                    comodel_name='product.product')

    @api.multi
    def action_copy_analysis_from(self):
        self.ensure_one()
        if self.copy_analysis_from and self.copy_analysis_from.analysis_ids:
            for line in self.copy_analysis_from.analysis_ids:
                new_line = line.copy()
                new_line.product_id = self.product_tmpl_id
        return self

    @api.multi
    def action_copy_data_from(self):
        self.ensure_one()
        fields_to_copy = (
            'sale_ok', 'hr_expense_ok', 'purchase_ok', 'type', 'uom_id',
            'lst_price', 'active', 'lot_label', 'qc_has_pis',
            'analytic_certificate', 'process_control', 'notes', 'qty', 'udm',
            'line', 'subline', 'container_id', 'base_form_id', 'clothing',
            'purchase_line', 'purchase_subline', 'country', 'customer',
            'packing_base', 'packing_production', 'packing_internal', 'packing',
            'box_elements', 'objective', 'categ_ids', 'cost_method', 'uom_po_id',
            'description_purchase', 'routing_ids', 'track_all', 'sequence_id',
            'state', 'product_manager', 'loc_rack', 'loc_row', 'loc_case',
            'life_time', 'use_time', 'removal_time', 'alert_time',
            'duration_type', 'warranty', 'sale_delay', 'produce_delay',
            'commission_exent', 'product_agent_ids', 'description_sale',
            'qc_aspects', 'qc_species', 'categ_id', 'property_account_income',
            'taxes_id', 'property_account_expense', 'supplier_taxes_id',
            'sii_exempt_cause', 'grouping', 'subgrouping'
        )
        swo_fields_to_copy = {
            'product_uom', 'group_id', 'product_min_action_qty',
            'product_min_qty', 'product_max_qty', 'from_date', 'to_date'
        }

        origin_product = self.copy_data_from
        if origin_product:
            dict = {}
            for field in fields_to_copy:
                if field in origin_product._fields:
                    dict[field] = getattr(origin_product, field)
#            dict['copy_analysis_from'] = origin_product
            self.with_context(disable_notify_changes = True).update(dict)

            # Quality analysis questions
#            self.action_copy_analysis_from()

            # Resupply rules
            if origin_product.orderpoint_ids and not self.orderpoint_ids:
                origin_swo = origin_product.orderpoint_ids[0]
                dict['name'] = self.name
                dict['product_id'] = self.id
                for field in swo_fields_to_copy:
                    if field in origin_swo._fields:
                        dict[field] = getattr(origin_swo, field)
                self.orderpoint_ids.create(dict)

            # Bill of materials
            if origin_product.bom_ids and not self.bom_ids:
                self.bom_ids.create({
                    'name': 'Lista (0): ' + self.name,
                    'product_id': self.id,
                    'product_tmpl_id': self.product_tmpl_id.id
                })

            # If origin product has process controls...
            pql = self.env['product.quality.limits']
            if pql.search([('name', '=', origin_product.product_tmpl_id.id)]):
                if not pql.search([('name', '=', self.product_tmpl_id.id)]):
                    pql.create({'name': self.product_tmpl_id.id})

        return self


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def action_copy_analysis_from(self):
        ctx = self.env.context.copy()
        ctx['active_ids'] = [self.id]
        view = self.env.ref('copy_from_ph.product_analysis_rel_wizard')
        return {
            'name': 'Copy analysis parameters from...',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.analysis.rel.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }
