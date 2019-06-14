# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.connector.connector import ConnectorEnvironment


def get_environment(session, model_name, backend_id):
    """ Create an environment to work with.  """
    backend_record = session.env['bananas.backend'].browse(backend_id)
    env = ConnectorEnvironment(backend_record, session, model_name)
    return env
