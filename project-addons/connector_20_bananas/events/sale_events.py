# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import _
from openerp.addons.connector.queue.job import job
from ..connector import get_environment
from ..backend import bananas
from openerp.addons.connector.unit.synchronizer import Importer
from ..unit.backend_adapter import GenericAdapter
from openerp.addons.connector.exception import IDMissingInBackend
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper
                                                  )


@bananas
class SaleOrderAdapter(GenericAdapter):
    _model_name = 'sale.order'
    _bananas_model = 'pedidos'


@job
def sale_order_import_batch(session, model_name, backend_id, date=None):
    """ Prepare a batch import of records from 20 bananas """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(SaleOrderBatchImport)
    importer.run(date)


@bananas
class SaleOrderBatchImport(Importer):
    _model_name = ['sale.order']

    def _import_record(self, record_id, date, **kwargs):
        """ Delay the import of the records"""
        import_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            record_id, date,
                            **kwargs)

    def run(self, date):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(
            date=date)
        for record_id in record_ids:
            self._import_record(record_id, date)


@job()
def import_record(session, model_name, backend_id, external_id, date,
                  force=False):
    """ Import a record from 20 bananas """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(SaleOrderImporter)
    importer.run(external_id, date, force=force)


@bananas
class SaleOrderImportMapper(ImportMapper):
    _model_name = 'sale.order'

    direct = [('comentarios', 'note'),
              ('idpedido', 'client_order_ref'),
              ('fecha', 'date_order'),
              ]

    children = [('productos', 'order_line', 'sale.order.line'),
                ]

    @mapping
    def partner_id(self, record):
        sale_partner = self.env['res.partner'].search(
            [('bananas_id', '=', int(record['codcliente']))])
        if sale_partner.parent_id:
            return {
                'partner_id': sale_partner.parent_id.id,
                'partner_shipping_id': sale_partner.id}
        else:
            return {'partner_id': sale_partner.id}

    @mapping
    def sale_channel(self, record):
        return {'sale_channel_id': self.env.ref(
            'connector_20_bananas.20_bananas_channel').id}


@bananas
class SaleOrderLineImportMapper(ImportMapper):
    _model_name = 'sale.order.line'

    direct = [('observaciones', 'customer_notes')]

    @mapping
    def product_id(self, record):
        return {'product_id': int(record['referencia'])}

    @mapping
    def quantity(self, record):
        if record['unidad'] == 'caja':
            product = self.env['product.product'].browse(
                int(record['referencia']))
            cantidad_unidades = record['cantidad'] * product.box_elements
            return {'product_uom_qty': cantidad_unidades}
        else:
            return{'product_uom_qty': record['cantidad']}


@bananas
class SaleOrderImporter(Importer):
    """ Base importer for 20 bananas """
    _model_name = ['sale.order']
    _base_mapper = SaleOrderImportMapper

    def __init__(self, connector_env):
        """
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(SaleOrderImporter, self).__init__(connector_env)
        self.bananas_id = None
        self.bananas_record = None

    def _get_bananas_data(self):
        """ Return the raw bananas data for ``self.bananas_id`` """
        return self.backend_adapter.read(self.bananas_id, self.date)

    def _map_data(self):
        """ Returns an instance of
        :py:class:`~openerp.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(self.bananas_record)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``_create`` or
        ``_update`` if some fields are missing or invalid.

        Raise `InvalidDataError`
        """
        return

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """
        if self.bananas_record['integradoERP10'] != '0':
            return True
        return

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    def _create(self, data):
        """ Create the OpenERP record """
        # special check on data before import
        self._validate_data(data)
        model = self.model.with_context(connector_no_export=True)
        binding = model.create(data)
        return binding

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        self.backend_adapter.update(
            self.bananas_id,
            {'idpedido': self.bananas_id, 'integradoERP10': '1'})
        backend = self.backend_record
        self.backend_adapter.send_message(
            binding.partner_id.bananas_id,
            backend.order_message.format(order=binding.client_order_ref), True)
        return

    def run(self, bananas_id, date, force=False):
        """ Run the synchronization

        :param bananas_id: identifier of the record on bananas
        """
        self.bananas_id = bananas_id
        self.date = date
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            bananas_id,
        )
        try:
            self.bananas_record = self._get_bananas_data()
        except IDMissingInBackend:
            return _('Record does no longer exist in bananas')
        skip = self._must_skip()
        if skip:
            return skip

        # Keep a lock on this import until the transaction is committed
        # The lock is kept since we have detected that the informations
        # will be updated into Odoo
        self.advisory_lock_or_retry(lock_name)

        map_record = self._map_data()

        record = self._create_data(map_record)
        binding = self._create(record)
        self._after_import(binding)
