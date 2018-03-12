# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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
import json
import logging
import werkzeug
import werkzeug.utils
from openerp.addons.web import http
from openerp.addons.web.http import request

_logger = logging.getLogger(__name__)

class WebsiteProtocol(http.Controller):

    # Url que se genera desde el wizard de impresión de protocolo, recibe producción y protocolo como parámetros
    # Los parámetros se recien de la forma <tipo_de_dato:nombre_de_parametro>
    @http.route(['/protocol/print/<model("mrp.production"):production>/<model("quality.protocol.report"):protocol>/<model("mrp.production.workcenter.line"):wkcenter_line>'],
                type='http', auth='user', website=True)
    def print_survey(self, production, protocol, wkcenter_line, **post):
        cr, uid, context2, session = request.cr, request.uid, request.context, request.session
        user_obj = request.registry['res.users']
        user = user_obj.browse(cr, uid, uid, context2)
        user_input_obj = request.registry['survey.user_input']
        view_obj = request.registry['ir.ui.view']
        context = {'production': production,
                   'protocol': protocol,
                   'wkcenter_line': wkcenter_line}
        # seq = 1

        # Se generar un surveyX por cada survey en el protocolo, luego la plantilla se encargará de parsear para cada uno el parámetro survey, que es el que usa internamente la vista genérica
        parts = []
        survey_responsed_ids = [x.survey_id.id for x in production.final_lot_id.response_ids]
        for line in protocol.report_line_ids:
            if line.survey_id:
                #context.update({'survey' + str(seq): line.survey_id})
                #seq += 1
                if line.survey_id.id not in survey_responsed_ids:
                    user_input_id = user_input_obj.create(cr, uid, {'survey_id': line.survey_id.id, 'partner_id': user.partner_id.id, 'lot_id': production.final_lot_id.id}, context2)
                    user_input = user_input_obj.browse(cr, uid, user_input_id, context2)
                    parts.append(('s',line.survey_id, user_input.token, line.show_sequence))
                    context.update({'exist': False})
                else:
                    response_id = user_input_obj.search(cr, uid, [('survey_id' ,'=', line.survey_id.id), ('lot_id' ,'=', production.final_lot_id.id)], context=context2)
                    response = user_input_obj.browse(cr, uid, response_id, context2)[0]
                    parts.append(('s',line.survey_id, response.token, line.show_sequence))
                    context.update({'exist': True})

            elif line.view_id:
                parts.append(('v',line.view_id.xml_id, line.show_sequence))
        context.update({'parts': parts})
        # renderiza la vista qweb con id protocol_print, de este módulo, pasándole en contexto production y tantos surveyX como surveys en el protocolo
        return request.website.render('quality_protocol_report.protocol_print',
                                      context)

    # return to form_view
    @http.route(['/quality_protocol/logout/<model("mrp.production"):production>'],
                type='http', methods=['GET'], auth='user')
    def logout(self, production, **get):
        cr, uid, context, session = request.cr, request.uid, request.context, request.session
        dataobj = request.registry['ir.model.data']
        menu_data_id = dataobj._get_id (cr, uid, 'mrp', 'menu_mrp_production_action')
        menu = dataobj.browse(cr, uid, menu_data_id, context).res_id
        action_data_id = dataobj._get_id (cr, uid, 'mrp', 'mrp_production_action')
        action = dataobj.browse(cr, uid, action_data_id, context).res_id
        return  werkzeug.utils.redirect('/web#id=%s&view_type=form&model=mrp.production&menu_id=%s&action=%s' % (production.id, menu, action))

    # AJAX submission of a survey
    @http.route(['/protocol/submit/<model("survey.survey"):survey>'],
                type='http', methods=['POST'], auth='user')
    def submit(self, survey, **post):
        """
            Función copiada de survey.
            TODO: es mejorable, sigue devolviendo la siguiente página aunque no se usa en el cliente.
        """
        _logger.debug('Incoming data: %s', post)
        cr, uid, context = request.cr, request.uid, request.context
        survey_obj = request.registry['survey.survey']
        questions_obj = request.registry['survey.question']
        page_obj = request.registry['survey.page']
        survey_id = int(post['survey_id'])


        # Answer validation
        errors = {}

        page_ids = page_obj.search(cr, uid, [('survey_id', '=', survey_id)], context=context)
        pages = page_obj.browse(cr, uid, page_ids, context=context)
        for page in pages:
            questions_ids = questions_obj.search(cr, uid, [('page_id', '=', page.id)], context=context)
            questions = questions_obj.browse(cr, uid, questions_ids, context=context)
            for question in questions:
                answer_tag = "%s_%s_%s" % (survey_id, page.id, question.id)
                errors.update(questions_obj.validate_question(cr, uid, question, post, answer_tag, context=context))

            ret = {}
            if (len(errors) != 0):
                # Return errors messages to webpage
                ret['errors'] = errors
            else:
                # Store answers into database
                user_input_obj = request.registry['survey.user_input']

                user_input_line_obj = request.registry['survey.user_input_line']
                try:
                    user_input_id = user_input_obj.search(cr, uid, [('token', '=', post['token'])], context=context)[0]
                except KeyError:  # Invalid token
                    return request.website.render("website.403")
                for question in questions:
                    answer_tag = "%s_%s_%s" % (survey_id, page.id, question.id)
                    user_input_line_obj.save_lines(cr, uid, user_input_id, question, post, answer_tag, context=context)

                user_input = user_input_obj.browse(cr, uid, user_input_id, context=context)
                go_back = post['button_submit'] == 'previous'
                next_page, _, last = survey_obj.next_page(cr, uid, user_input, page.id, go_back=go_back, context=context)
                vals = {'last_displayed_page_id': page.id}
                if next_page is None and not go_back:
                    vals.update({'state': 'done'})
                else:
                    vals.update({'state': 'skip'})
                user_input_obj.write(cr, uid, user_input_id, vals, context=context)
                ret['redirect'] = '/survey/fill/%s/%s' % (survey.id, post['token'])
                if go_back:
                    ret['redirect'] += '/prev'
        return json.dumps(ret)


    # AJAX prefilling of a survey
    @http.route(['/protocol/fill/<model("survey.survey"):survey>/<string:token>'],
                type='http', auth='public', website=True)
    def fill_data(self, survey, token, **post):
        print "ENTRA"
        cr, uid, context = request.cr, request.uid, request.context
        user_input_line_obj = request.registry['survey.user_input_line']
        ret = {}

        ids = user_input_line_obj.search(cr, uid, [('user_input_id.token', '=', token)], context=context)
        answers = user_input_line_obj.browse(cr, uid, ids, context=context)

        # Return non empty answers in a JSON compatible format
        for answer in answers:
            if not answer.skipped:
                answer_tag = '%s_%s_%s' % (answer.survey_id.id, answer.page_id.id, answer.question_id.id)
                answer_value = None
                if answer.answer_type == 'free_text':
                    answer_value = answer.value_free_text
                elif answer.answer_type == 'text' and answer.question_id.type == 'textbox':
                    answer_value = answer.value_text
                elif answer.answer_type == 'text' and answer.question_id.type != 'textbox':
                    # here come comment answers for matrices, simple choice and multiple choice
                    answer_tag = "%s_%s" % (answer_tag, 'comment')
                    answer_value = answer.value_text
                elif answer.answer_type == 'number':
                    answer_value = answer.value_number.__str__()
                elif answer.answer_type == 'date':
                    answer_value = answer.value_date
                elif answer.answer_type == 'suggestion' and not answer.value_suggested_row:
                    answer_value = answer.value_suggested.id
                elif answer.answer_type == 'suggestion' and answer.value_suggested_row:
                    answer_tag = "%s_%s" % (answer_tag, answer.value_suggested_row.id)
                    answer_value = answer.value_suggested.id
                if answer_value:
                    dict_soft_update(ret, answer_tag, answer_value)
                else:
                    _logger.warning("[survey] No answer has been found for question %s marked as non skipped" % answer_tag)
        return json.dumps(ret)

def dict_soft_update(dictionary, key, value):
    ''' Insert the pair <key>: <value> into the <dictionary>. If <key> is
    already present, this function will append <value> to the list of
    existing data (instead of erasing it) '''
    if key in dictionary:
        dictionary[key].append(value)
    else:
        dictionary.update({key: [value]})
