# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import requests

from openerp.addons.connector.exception import (
    NetworkRetryableError,
    RetryableJobError,
)
from openerp.addons.connector.unit.backend_adapter import CRUDAdapter


class BananasCRUDAdapter(CRUDAdapter):
    """ External Records Adapter for 20 bananas """

    def make_request(self, data, url_model, method, custom_headers={}):
        backend = self.backend_record
        url = "%s/%s" % (backend.location, url_model)
        headers = {
            "apikey": backend.api_key,
            "Content-Type": "application/json",
        }
        if custom_headers:
            headers.update(custom_headers)
        result = requests.request(method, url, headers=headers, json=data)
        return result

    def _search(self, model, date):
        """ Search records according to some criterias
        and returns a list of ids """
        backend = self.backend_record
        url = "%s/%s/%s" % (backend.location, model, date)
        headers = {
            "apikey": backend.api_key,
            "Content-Type": "application/json",
        }
        result = requests.request("GET", url, headers=headers)
        if result.status_code in [
            400,  # Service unavailable
            401,
            502,  # Bad gateway
            503,  # Service unavailable
            504,
        ]:  # Gateway timeout
            raise RetryableJobError(
                "A protocol error caused the failure of the job:\n"
                "URL: %s\n"
                "HTTP/HTTPS headers: %s\n"
                "Error code: %d\n"
                % (result.url, result.headers, result.status_code)
            )
        return [x["idpedido"] for x in result.json()["records"]]

    def _read(self, model, id, date):
        """ Search records according to some criterias
        and returns a list of ids """
        backend = self.backend_record
        url = "%s/%s/%s" % (backend.location, model, date)
        headers = {
            "apikey": backend.api_key,
            "Content-Type": "application/json",
        }
        result = requests.request("GET", url, headers=headers)
        records = result.json()["records"]
        if records:
            for record in records:
                if record["idpedido"] == id:
                    return record
        return []

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, model, data):
        """ Create a record on the external system """
        try:
            response = self.make_request(data, model, "POST")
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as err:
            raise NetworkRetryableError(
                "A network error caused the failure of the job: " "%s" % err
            )
        if response.status_code in [
            400,  # Service unavailable
            401,
            502,  # Bad gateway
            503,  # Service unavailable
            504,
        ]:  # Gateway timeout
            raise RetryableJobError(
                "A protocol error caused the failure of the job:\n"
                "URL: %s\n"
                "HTTP/HTTPS headers: %s\n"
                "Error code: %d\n"
                % (response.url, response.headers, response.status_code)
            )
        return response

    def write(self, model, data):
        """ Update records on the external system """
        try:
            response = self.make_request(data, model, "PUT")
            if response.status_code in [
                400,
                401,
                502,  # Bad gateway
                503,  # Service unavailable
                504,
            ]:  # Gateway timeout
                raise RetryableJobError(
                    "A protocol error caused the failure of the job:\n"
                    "URL: %s\n"
                    "HTTP/HTTPS headers: %s\n"
                    "Error code: %d\n"
                    % (response.url, response.headers, response.status_code)
                )
            return response
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as err:
            raise NetworkRetryableError(
                "A network error caused the failure of the job: " "%s" % err
            )
        else:
            raise

    def delete(self, model, id=False):
        """ Update records on the external system """
        try:
            response = self.make_request(id, model, "DELETE")
            if response.status_code in [
                400,
                401,
                502,  # Bad gateway
                503,  # Service unavailable
                504,
            ]:  # Gateway timeout
                raise RetryableJobError(
                    "A protocol error caused the failure of the job:\n"
                    "URL: %s\n"
                    "HTTP/HTTPS headers: %s\n"
                    "Error code: %d\n"
                    % (response.url, response.headers, response.status_code)
                )
            return response
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as err:
            raise NetworkRetryableError(
                "A network error caused the failure of the job: " "%s" % err
            )
        else:
            raise
        """ Delete a record on the external system """


class GenericAdapter(BananasCRUDAdapter):

    _model_name = None
    _bananas_model = None
    _delete_id_in_url = False

    def insert(self, data):
        """ Create a record on the external system """
        return self.create(self._bananas_model, [data])

    def search(self, date):
        return self._search(self._bananas_model, date)

    def read(self, id, date):
        """
            Solo se usa para pedidos, y no hay manera de leer el pedido por id
            Debemos leer todos los del día y buscar en los datos
        """
        return self._read(self._bananas_model, id, date)

    def update(self, id, data):
        """ Update records on the external system """
        return self.write(self._bananas_model, [data])

    def remove(self, id):
        """ Delete a record on the external system """
        if self._delete_id_in_url:
            return self.delete(self._bananas_model + "/*/%s" % str(id))
        else:
            return self.delete(self._bananas_model, [str(id)])

    def remove_vals(self, data):
        return self.delete(self._bananas_model, [data])

    def insert_whitelist(self, data):
        return self.create("listablanca", [data])

    def clean_whitelist(self, partner_id):
        self.make_request(
            [{"codcliente": partner_id}],
            "listablanca",
            "DELETE",
            custom_headers={"imsure": 'true'},
        )

    def remove_whitelist(self, partner_id, product_id):
        self.make_request(
            [{"codcliente": partner_id, 'codproducto': product_id}],
            "listablanca",
            "DELETE",
        )

    def send_message(self, partner_id, message, central=False):
        response = self.create(
            "notificacion/%s" % partner_id,
            {"mensaje": message, "comolacentral": central},
        )
        if not response.json()["sended"]:
            raise Exception("message not sended")
