from openerp import models, api
from urlparse import urljoin

@api.one
def editable_report_url(self, view_id, relative_url=False, target_id=False):
    config = self.env['ir.config_parameter']
    if relative_url:
        base_url = '/'
    elif config.get_param('phamtomjs_base_url'):
        base_url = self.env['ir.config_parameter']. \
            get_param('phamtomjs_base_url')
    else:
        base_url = config.get_param('web.base.url')

    target_id = self.id if not target_id else target_id
    return urljoin(
        base_url,
        'editable_report/print/{}/{}'.format(view_id, target_id)
    )
models.BaseModel.editable_report_url = editable_report_url

@api.multi
def editable_report_form(self, view_id, target_id=False):
    form_url = {
        'type': 'ir.actions.act_url',
        'name': 'Editable report form',
        'target': 'new',
        'url': self.editable_report_url(view_id, True, target_id)[0],
    }
    return form_url
models.BaseModel.editable_report_form = editable_report_form

@api.multi
def editable_report_print(self, view_id, target_id=False):
    report_url = self.editable_report_url(view_id, False, target_id)[0]
    return self.env['editable.report'].print_report(report_url)
models.BaseModel.editable_report_print = editable_report_print
