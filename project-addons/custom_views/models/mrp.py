# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    _order = 'name'


class MrpProcedureType(models.Model):
    _name = 'mrp.procedure.type'
    _description = 'Procedures (SOP) types'

    name = fields.Char('Type of procedure', required=True)
    code = fields.Char('Type code', required=True)


class MrpProcedure(models.Model):
    _name = 'mrp.procedure'
    _description = 'Standard Operating Procedures (SOP)'

    name = fields.Char('Procedure (SOP)', required=True)
    revision = fields.Char('Version', required=True)
    type_id = fields.Many2one(comodel_name='mrp.procedure.type',
                              string='Type of procedure', required=True)
    date_authorized = fields.Date('Date authorized')
    date_validated = fields.Date('Date validated')
    title = fields.Text('Title')
    notes = fields.Text('Notes')
    medicine = fields.Boolean(default=False)
    active = fields.Boolean(default=True)
    attachment = fields.Binary(compute='_return_attachment')
    attachment_filename = fields.Char(compute='_return_attachment')

    @api.one
    def _return_attachment(self):
        attachment_id = self.env['ir.attachment'].search(
            [('res_model', '=', 'mrp.procedure'),
             ('res_id', '=', self.id)], limit=1, order='id desc'
        )
        try:
            self.attachment = attachment_id.datas if attachment_id else False
            self.attachment_filename = attachment_id.name
        except OSError as e:
            pass

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = rec.name + ' (rev. ' + rec.revision + ')'
            res.append((rec.id, name))
        return res


class MrpProcedureType_(models.Model):
    _inherit = 'mrp.procedure.type'

    procedure_ids = fields.One2many(comodel_name='mrp.procedure',
                                    inverse_name='type_id',
                                    string='Standard Operating Procedures (SOP)')


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    sop_manufacturing_id = fields.Many2one(
        comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'routing_manufacturing')]",
        string='Manufacturing procedure')
    sop_handling_id = fields.Many2one(
        comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'routing_handling')]",
        string='Handling procedure')


class MrpMachinery(models.Model):
    _name = 'mrp.machinery'
    _description = 'Production machinery'

    name = fields.Char('Machine', required=True)
    accept_more_than_one_raw_material = fields.Boolean(
        string='Accept more than one raw material?',
        default=False)
    sop_cleaning_product_campaign_id = fields.Many2one(
        comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'machine_cleaning_product_campaign')]",
        string='Cleaning for product or campaign change procedure')
    sop_cleaning_maintenance_id = fields.Many2one(
        comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'machine_cleaning_maintenance')]",
        string='Cleaning and maintenance procedure')
    sop_operations_id = fields.Many2one(
        comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'machine_operations')]",
        string='Operations procedure')
    sop_maintenance_id = fields.Many2one(
        comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'machine_maintenance')]",
        string='Maintenance procedure')
    sop_extra_1_id = fields.Many2one(
        comodel_name='mrp.procedure',
        domain="[('type_id.code', '=', 'machine_extra_1')]",
        string='Extra 1 procedure')
    routing_ids = fields.Many2many(comodel_name='mrp.routing')


class MrpRouting_(models.Model):
    _inherit = 'mrp.routing'

    machinery_ids = fields.Many2many(comodel_name='mrp.machinery')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def write(self, vals, update=True, mini=True):
        if vals.get('final_lot_id', False):
            lot = self.env['stock.production.lot'].browse(vals['final_lot_id'])
            lot.mrp_id = self.id
        return super(MrpProduction, self).write(vals, update=update, mini=mini)
