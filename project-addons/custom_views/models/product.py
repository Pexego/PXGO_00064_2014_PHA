# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp
import datetime
import operator


class ProductProductAnalysisMethod(models.Model):
    _name = 'product.product.analysis.method'

    product_id = fields.Many2one(comodel_name='product.product')
    procedure_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'quality_control_analysis_methods')]",
        string='Analysis method')
    attachment = fields.Binary(
        related='procedure_id.attachment', readonly=True)
    filename = fields.Char(
        related='procedure_id.attachment_filename', readonly=True)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_commercial_name = fields.Char()
    is_in_current_pricelist = fields.Boolean(
        compute='_compute_is_in_current_pricelist',
        search='_search_is_in_current_pricelist')
    year_appearance = fields.Integer('Year of appearance',
        default=datetime.datetime.now().year)
    manufacturing_procedure_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'product_manufacturing')]",
        string='Manufacturing procedure')
    manufacturing_procedure_attachment = fields.Binary(
        related='manufacturing_procedure_id.attachment', readonly=True)
    manufacturing_procedure_filename = fields.Char(
        related='manufacturing_procedure_id.attachment_filename', readonly=True)
    packaging_procedure_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'product_packaging')]",
        string='Packaging procedure')
    packaging_procedure_attachment = fields.Binary(
        related='packaging_procedure_id.attachment', readonly=True)
    packaging_procedure_filename = fields.Char(
        related='packaging_procedure_id.attachment_filename', readonly=True)
    generic_specification_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', 'ilike', 'specifications%')]",
        string='Specification')
    generic_specification_attachment = fields.Binary(
        related='generic_specification_id.attachment', readonly=True)
    generic_specification_filename = fields.Char(
        related='generic_specification_id.attachment_filename', readonly=True)
    model_specification_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', 'ilike', 'specifications%')]",
        string='Model specification')
    model_specification_attachment = fields.Binary(
        related='model_specification_id.attachment', readonly=True)
    model_specification_filename = fields.Char(
        related='model_specification_id.attachment_filename', readonly=True)
    analysis_method_ids = fields.One2many(
        comodel_name='product.product.analysis.method',
        inverse_name='product_id', string="Analysis method")
    analysis_plan_id = fields.Many2one(comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'quality_control_analysis_plans')]",
        string='Analysis plan')
    analysis_plan_attachment = fields.Binary(
        related='analysis_plan_id.attachment', readonly=True)
    analysis_plan_filename = fields.Char(
        related='analysis_plan_id.attachment_filename', readonly=True)
    notes = fields.Text()
    reception_warehouse_warning = fields.Text()
    width = fields.Float()
    height = fields.Float()
    depth = fields.Float()
    earliest_picking = fields.Date(compute='_earliest_picking',
                                   search='_search_earliest_picking')
    obsolete = fields.Boolean(default=False)

    @api.one
    @api.constrains('year_appearance')
    def _check_year_of_appearance(self):
        current_year = datetime.datetime.now().year
        if 1956 >= self.year_appearance <= current_year:
            raise Warning(_('Year must be between 1956 and %s.') %
                          (current_year,))

    @api.one
    @api.constrains('active')
    def _update_template_active(self):
        if self.product_tmpl_id.active != self.active:
            self.product_tmpl_id.write({'active': self.active})

    @api.multi
    def name_get(self):  # Hide default_code by default
        return super(ProductProduct,
                     self.with_context(display_default_code=False)).name_get()

    @api.depends('pricelist_id')
    def _compute_is_in_current_pricelist(self):
        pricelist = self.pricelist_id.mapped('id')
        return self.env.context.get('pricelist', False) in pricelist

    def _search_is_in_current_pricelist(self, operator, value):
        # This domain filter by price list is for sale orders that aren't for
        # sample/advertising purposes
        if self.env.context.get('is_a_sample_order', False):
            return [('active', '=', True)]

        current_pricelist_product_list = []
        pricelist = self.env.context.get('pricelist', False)
        if pricelist:
            pricelist_id = self.env['product.pricelist'].browse(pricelist)
            current_pricelist_product_list = \
                pricelist_id.version_id.items_id.mapped('product_id.id')
        if ((operator == '=') and value) or ((operator == '!=') and not value):
            operator = 'in'
        else:
            operator = 'not in'
        return [('id', operator, current_pricelist_product_list)]

    @api.one
    def _earliest_picking(self):
        picking_id = self.env['stock.picking'].search([
            ('move_lines.product_id', '=', self.id),
            ('state', 'not in', ('done', 'cancel')),
            ('picking_type_code', '=', 'outgoing')
        ], limit=1, order='max_date')
        self.earliest_picking = picking_id.max_date if picking_id else False

    @api.multi
    def _search_earliest_picking(self, relate, value):
        def get_truth(inp, relate, cut):
            ops = {'>': operator.gt,
                   '<': operator.lt,
                   '>=': operator.ge,
                   '<=': operator.le,
                   '=': operator.eq,
                   '!=': operator.ne}
            return ops[relate](inp, cut)

        product_ids = self.search([]).filtered(
            lambda p: get_truth(p.earliest_picking, relate, value)
        )
        return [('id', 'in', product_ids.ids)]

    @api.multi
    def product_price_history_action(self):
        self.ensure_one()
        return self.product_tmpl_id.product_price_history_action()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    suppliers_pricelists = fields.One2many('pricelist.partnerinfo',
                                 compute='_suppliers_pricelists')
    cost_price_rm = fields.Float('Raw material cost price',
                                 digits=dp.get_precision('Product Price'))
    cost_price_components = fields.Float('Components cost price',
                                 digits=dp.get_precision('Product Price'))
    cost_price_dl = fields.Float('Direct labor cost price',
                                 digits=dp.get_precision('Product Price'))
    cost_eval_price_method = fields.Char('Costing Method',
                                   compute='_cost_eval_method')
    cost_eval_price = fields.Float('Product cost evaluation',
                                 digits=dp.get_precision('Product Price'))
    cost_eval_price_rm = fields.Float('Raw material cost evaluation price',
                                 digits=dp.get_precision('Product Price'))
    cost_eval_price_components = fields.Float('Components cost evaluation price',
                                 digits=dp.get_precision('Product Price'))
    cost_eval_price_dl = fields.Float('Direct labor cost evaluation price',
                                 digits=dp.get_precision('Product Price'))
    internal_scrapped_qty = fields.Float('Stock at internal scrap location',
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly = True)
    virtual_conservative = fields.Float('Virtual stock conservative',
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly=True)
    out_of_existences = fields.Float('Out of existences',
                             digits=dp.get_precision('Product Unit of Measure'),
                             readonly=True)
    out_of_existences_dismissed = fields.Float('Out of existences dismissed',
                             digits=dp.get_precision('Product Unit of Measure'),
                             readonly=True)
    real_incoming_qty = fields.Float('Real incoming qty.',
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly=True)
    production_planning_qty = fields.Float(
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly=True)
    pre_production_qty = fields.Float(
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly=True)
    stock_move_ids = fields.One2many(string='Stock movements',
                                     comodel_name='stock.move',
                                     inverse_name='product_id')
    ecoembes_weight = fields.Float(digits = dp.get_precision('Stock Weight'))

    @api.one
    @api.depends('seller_ids')
    def _suppliers_pricelists(self):
        ids = []
        for product in self:
            for seller in product.seller_ids:
                for pricelist in seller.pricelist_ids:
                    ids.append(pricelist.id)
        self.suppliers_pricelists = ids

    @api.one
    def _cost_eval_method(self):
        self.cost_eval_price_method = _('Cost eval (night calculation)')

    @api.multi
    def compute_detailed_stock(self):
        warehouses = self.env['stock.warehouse'].search([])
        stock_ids = [wh.lot_stock_id.id for wh in warehouses]

        for product in self:
            if not product.product_variant_ids:
                continue

            product_id = product.product_variant_ids[0]

            quants = self.env['stock.quant'].search([
                ('product_id', '=', product_id.id),
                ('location_id.usage', '=', 'internal'),
                ('location_id.scrap_location', '=', True)
            ])
            internal_scrapped_qty = sum(quant.qty for quant in quants)

            wh = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.user.company_id.id)])
            input_location_ids = wh.wh_input_stock_loc_id._get_child_locations()
            quants = self.env['stock.quant'].search([
                ('product_id', '=', product_id.id),
                ('location_id.id', 'in', input_location_ids.ids)
            ])
            input_qty = sum(quant.qty for quant in quants)
            virtual_conservative = product.qty_available - input_qty - \
                                   product.outgoing_qty - internal_scrapped_qty

            production_planning_orders = self.env['production.planning.orders'].\
                search([('product_id', '=', product_id.id),
                        ('compute', '=', True)])
            production_planning_qty = sum(order.product_qty for order in
                                          production_planning_orders)
            prod_plan_materials = self.env['production.planning.materials'].\
                search([('product_id', '=', product_id.id)])
            production_planning_qty -= sum(material.qty_required for material in
                                           prod_plan_materials)

            production_orders = self.env['mrp.production'].\
                search([('product_id', '=', product_id.id),
                        ('state', '=', 'draft')])
            pre_production_qty = sum(order.product_qty for order in
                                     production_orders)
            pre_prod_materials = self.env['stock.move'].\
                search([('product_id', '=', product_id.id),
                        ('raw_material_production_id', '!=', False),
                        ('raw_material_production_id.state', 'in',
                         ('draft', 'confirmed')),
                        ('state', '=', 'waiting')])
            pre_production_qty -= sum(material.product_uom_qty for material in
                                      pre_prod_materials)

            quants = self.env['stock.quant'].search([
                ('product_id', '=', product_id.id),
                ('location_id.usage', '=', 'internal'),
                '!', ('location_id', 'child_of', stock_ids),
                '|',
                ('location_id.scrap_location', '=', False),
                '&',
                ('location_id.scrap_location', '=', True),
                ('location_id.dismissed_location', '=', False),
            ])
            out_of_existences = sum(quant.qty for quant in quants)

            quants = self.env['stock.quant'].search([
                ('product_id', '=', product_id.id),
                ('location_id.usage', '=', 'internal'),
                '!', ('location_id', 'child_of', stock_ids),
                ('location_id.scrap_location', '=', True),
                ('location_id.dismissed_location', '=', True),
            ])
            out_of_existences_dismissed = sum(quant.qty for quant in quants)

            moves = self.env['stock.move'].search([
                ('product_id', '=', product_id.id),
                ('state', 'in', ('assigned', 'confirmed', 'waiting')),
                ('picking_id.picking_type_id.code', '=', 'incoming'),
                ('location_id.usage', '!=', 'internal'),
                ('location_dest_id.usage', '=', 'internal')
            ])
            real_incoming_qty = sum(move.product_uom_qty for move in moves)

            product.with_context(disable_notify_changes = True).write({
                'internal_scrapped_qty': internal_scrapped_qty,
                'virtual_conservative': virtual_conservative,
                'production_planning_qty': production_planning_qty,
                'pre_production_qty': pre_production_qty,
                'out_of_existences': out_of_existences,
                'out_of_existences_dismissed': out_of_existences_dismissed,
                'real_incoming_qty': real_incoming_qty})

            product_id.with_context(disable_notify_changes = True). \
                update_qty_in_production()

    @api.multi
    def product_price_history_action(self):
        view_id = self.env.ref('custom_views.product_price_history_tree')
        return {
            'name': 'Histórico de precios de coste',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'product.price.history',
            'views': [(view_id.id, 'tree')],
            'view_id': view_id.id,
            'target': 'new',
            'context': self.with_context({
                    'active_id': self.id,
                    'active_model': self._name,
                    'search_default_product_template_id': self.id,
                }).env.context,
        }


class PricelistPartnerinfo(models.Model):
    _inherit = 'pricelist.partnerinfo'

    sequence = fields.Integer(related='suppinfo_id.sequence', readonly=True)


class ProductIncoming(models.TransientModel):
    _name = 'product.incoming'
    _inherits = {'product.product': 'product_id'}
    _rec_name = 'product_id'

    product_id = fields.Many2one(string='Product',
                                 comodel_name='product.product', required=True,
                                 ondelete='cascade', readonly=True)
    data_uid = fields.Many2one(comodel_name='res.users', readonly=True)
    cumulative_incoming_qty = fields.Float(default=0, readonly=True)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        self.env.cr.execute('delete from product_incoming where data_uid = {:d}'.
                            format(self.env.user.id))

        query = """
            insert into product_incoming (id, product_id,
                cumulative_incoming_qty, data_uid,
                create_uid, create_date, write_uid, write_date)
            select
                row_number() over (order by pp.name_template) as id,
                pp.id as product_id,
                sum(sm.product_uom_qty),
                {0:d} as data_uid,
                {0:d} as create_uid,
                current_date as create_date,
                {0:d} as write_uid,
                current_date as write_date                
            from product_product pp
            join stock_move sm on sm.product_id = pp.id
             and sm.state = 'done'
             and sm.location_id = {1:d}  -- Suppliers locations
             and sm.location_dest_id = {2:d}  -- Company incoming location            
        """
        group_by = """
            group by 2, 4, 5, 6, 7
            having sum(sm.product_uom_qty) != 0
        """

        if self.env.context.get('date_start', False):
            query += """ where sm.date between '{3}' and '{4}'""" + group_by
            self.env.cr.execute(query.format(
                self.env.user.id,
                self.env.ref('stock.stock_location_suppliers').id,
                self.env.ref('stock.stock_location_company').id,
                self.env.context.get('date_start'),
                self.env.context.get('date_end')
            ))
        else:
            query += group_by
            self.env.cr.execute(query.format(
                self.env.user.id,
                self.env.ref('stock.stock_location_suppliers').id,
                self.env.ref('stock.stock_location_company').id
            ))

        return super(ProductIncoming, self).search(args, offset=offset,
                                                   limit=limit, order=order,
                                                   count=count)