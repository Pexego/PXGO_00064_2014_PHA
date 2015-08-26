# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
from openerp import models, fields, api


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    quality_survey = fields.Boolean('Quality survey')

    @api.multi
    def write(self, vals):
        res = super(SurveySurvey, self).write(vals)
        if vals.get('quality_survey', False):
            for survey in self:
                for page in survey.page_ids:
                    page.quality_survey = survey.quality_survey
                    for question in page.question_ids:
                        question.quality_survey = survey.quality_survey
                        for label in question.labels_ids:
                            label.quality_survey = survey.quality_survey
                for user_input in survey.user_input_ids:
                    user_input.quality_survey = survey.quality_survey
                    for line in user_input.user_input_line_ids:
                        line.quality_survey = survey.quality_survey
        return res


class SurveyPage(models.Model):
    _inherit = 'survey.page'

    quality_survey = fields.Boolean('Quality survey')

    @api.model
    def create(self, vals):
        res = super(SurveyPage, self).create(vals)
        res.quality_survey = res.survey_id.quality_survey
        return res


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    quality_survey = fields.Boolean('Quality survey')

    @api.model
    def create(self, vals):
        res = super(SurveyQuestion, self).create(vals)
        res.quality_survey = res.survey_id.quality_survey
        return res


class SurveyLabel(models.Model):
    _inherit = 'survey.label'

    quality_survey = fields.Boolean('Quality survey')

    @api.model
    def create(self, vals):
        res = super(SurveyQuestion, self).create(vals)
        res.quality_survey = res.question_id.quality_survey
        return res


class survey_user_input(models.Model):
    _inherit = 'survey.user_input'

    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    quality_survey = fields.Boolean('Quality survey')

    @api.model
    def create(self, vals):
        res = super(survey_user_input, self).create(vals)
        res.quality_survey = res.survey_id.quality_survey
        return res


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input_line'

    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    quality_survey = fields.Boolean('Quality survey')

    @api.model
    def create(self, vals):
        res = super(SurveyUserInputLine, self).create(vals)
        res.quality_survey = res.survey_id.quality_survey
        return res
