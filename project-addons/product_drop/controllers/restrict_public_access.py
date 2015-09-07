import openerp.http as http
from openerp.http import request
import re


class RestrictPublicAccess(http.Controller):
    @http.route('/product_drop/parameters.js', type="http")
    def send_js_parameters(self):
        addr = request.httprequest.environ['REMOTE_ADDR']
        authorizedAddresses = http.request.env['ir.config_parameter'].get_param('product_drop.authorized_addresses')
        authorizedAddresses = authorizedAddresses.replace('*', '\d{1,3}')
        authorized = False
        for pattern in authorizedAddresses.split():
            pattern = '^' + pattern + '$'
            pat = re.compile(pattern)
            authorized = authorized or pat.match(addr)

        if (authorized):
            xmlrpcUser = http.request.env['ir.config_parameter'].get_param('product_drop.xmlrpc_user')
            xmlrpcPass = http.request.env['ir.config_parameter'].get_param('product_drop.xmlrpc_password')
            database = http.request.env.cr.dbname
            server, port = request.httprequest.host.split(':')

            return """var odooObj = new OdooXmlRpc(
                '%s',
                '%s',
                '%s',
                'http://',
                '%s',
                '%s'
            );""" % (xmlrpcUser, xmlrpcPass, database, server, port)
        else:
            redirect = """
                alert('ACCESS DENIED!\\n\\nCONTACT SITE ADMIN TO REQUEST ACCESS.');
                window.location = '%s';
            """ % (request.httprequest.host_url)
            return redirect
