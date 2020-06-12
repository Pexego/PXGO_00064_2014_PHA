# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from ..connector import get_environment
from datetime import datetime, timedelta
import pytz


def _get_exporter(session, model_name, record_id, class_exporter):
    backend = session.env["bananas.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    return env.get_connector_unit(class_exporter)


def get_next_execution_time(session):
    backend = session.env["bananas.backend"].search([])[0]
    start_execution_hour = backend.start_execution_hour
    end_execution_hour = backend.stop_execution_hour
    if not start_execution_hour and not end_execution_hour:
        return 0
    now = datetime.now(pytz.timezone(backend.env.user.tz))
    if now.hour > end_execution_hour:
        execution_day = now + timedelta(days=1)
    elif now.hour < start_execution_hour:
        execution_day = now
    else:
        return 0
    next_execution = pytz.timezone(backend.env.user.tz).localize(datetime(
        execution_day.year,
        execution_day.month,
        execution_day.day,
        start_execution_hour,
    ))
    # Añadimos 30 segundos para evitar problemas
    return int((next_execution - now).total_seconds()) + 30
