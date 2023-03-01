# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    prestashop_zero_stock = fields.Boolean('Prestashop zero stock')


class PrestashopProductTemplate(models.Model):
    _inherit = 'prestashop.product.template'

    @api.multi
    def recompute_prestashop_qty(self):
        self.filtered('prestashop_zero_stock').write({'quantity': 0.0})
        return super(PrestashopProductTemplate,
                     self.filtered(lambda p: not p.prestashop_zero_stock)).\
            recompute_prestashop_qty()


class PrestashopProductCombination(models.Model):
    _inherit = "prestashop.product.combination"

    main_template_id = fields.Many2one(
        required=False,
    )

    # _sql_constraints = [
    #     ('prestashop_product_combination_prestashop_erp_uniq', 'Check(1=1)',
    #      'A record with same ID already exists on PrestaShop.'),
    # ]

    def init(self, cr):
        cr.execute(
            "alter table prestashop_product_combination "
            "drop constraint if exists "
            "prestashop_product_combination_prestashop_erp_uniq"
        )
        return True

    @api.multi
    def recompute_prestashop_qty(self):
        self.filtered('prestashop_zero_stock').write({'quantity': 0.0})
        return super(PrestashopProductCombination,
                     self.filtered(lambda p: not p.prestashop_zero_stock)).\
            recompute_prestashop_qty()


class ProductPrestashopNeedExportStock(models.Model):
    _name = 'product.prestashop.need.export.stock'

    product_id = fields.Integer(index=True)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def update_prestashop_qty(self):
        flags = self.env['product.prestashop.need.export.stock']
        if self._context.get('cron_compute'):
            flags.search([('product_id', 'in', self.ids)]).unlink()
            for product_id in self:
                boms = self.env['mrp.bom'].search(
                    [('bom_line_ids.product_id', '=', product_id.id)]
                )
                if boms:
                    self = (
                        self
                        + boms.mapped('product_tmpl_id.product_variant_ids')
                        + boms.mapped('product_id')
                    )
            for product_id in self:
                product_id.product_tmpl_id.update_prestashop_quantities()
                # Recompute qty in combination binding
                for combination_binding in product_id.prestashop_bind_ids:
                    combination_binding.recompute_prestashop_qty()
                for combination_binding in product_id.\
                        prestashop_combinations_bind_ids:
                    combination_binding.recompute_prestashop_qty()
        else:
            """
            # Raise flag only for products linked with PrestaShop
            new_ids = list(
                set(self.filtered(lambda p: p.prestashop_bind_ids or
                                            p.prestashop_combinations_bind_ids)
                        .ids)
                - set(flags.search([('product_id', 'in', self.ids)])
                           .mapped('product_id'))
            )
            """
            new_ids = list(
                set(self.ids)
                - set(flags.search([('product_id', 'in', self.ids)])
                           .mapped('product_id'))
            )
            for id in new_ids:
                flags.create({'product_id': id})

    @api.model
    def cron_export_custom_stock(self):
        flags = self.env['product.prestashop.need.export.stock'].search([])
        product_ids = flags.mapped('product_id')
        if product_ids:
            self.browse(product_ids).with_context(cron_compute=True)\
                .update_prestashop_qty()
        return True
