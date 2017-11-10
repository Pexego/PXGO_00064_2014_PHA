# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, exceptions, _


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    @api.model
    def next_sequence(self):
        if not self.ids:
            return False
        force_company = self.env.context.get('force_company')
        if not force_company:
            force_company = self.env.user.company_id.id
        sequences = self.read(['name', 'company_id', 'implementation',
                               'number_next_actual', 'prefix', 'suffix', 'padding'])
        preferred_sequences = [s for s in sequences if
                               s['company_id'] and
                               s['company_id'][0] == force_company]
        seq = preferred_sequences[0] if preferred_sequences else sequences[0]

        d = self._interpolation_dict_context(context=self.env.context)
        try:
            interpolated_prefix = self._interpolate(seq['prefix'], d)
            interpolated_suffix = self._interpolate(seq['suffix'], d)
        except ValueError:
            raise exceptions.Warning(_('Warning'),
                                     _('Invalid prefix or suffix for sequence'
                                       ' \'%s\'') % (seq.get('name')))
        return interpolated_prefix + '%%0%sd' % seq['padding'] % \
               seq['number_next_actual'] + interpolated_suffix