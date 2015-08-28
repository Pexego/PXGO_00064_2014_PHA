/********************************************************************
 * Clase para encapsular y simplificar las llamadas XMLRPC a Odoo
 * En un primer momento, se hizo para el protocolo antiguo, pero
 * surgió la necesidad de pasar más parámetros (kw) y se retocó lo
 * que hizo falta en ese momento. Falta pasar todos los demás métodos
 * al nuevo protocolo.
 ********************************************************************/

function OdooXmlRpc(user, pass, dbname, authority, server, port) {
    var uid = 0;
    this.user = $.xmlrpc.force('string', user);
    this.pass = $.xmlrpc.force('string', pass);
    this.dbName = $.xmlrpc.force('string', dbname);
    this.authority = authority;
    this.server = server;
    this.port = port;
    this.serverUrl = authority + server + ':' + port + '/xmlrpc/2/';

    this.login = function(onResponseOK) {
        $.xmlrpc({
            url: this.serverUrl + 'common',
            methodName: 'login',
            dataType: 'jsonrpc',
            params: [this.dbName, this.user, this.pass],
            success: function (response, status, jqXHR) {
                uid = $.xmlrpc.force('int', response);
                onResponseOK();
            },
            error: function (jqXHR, status, error) {
                alert(jqXHR + '-' + status + '-' + error);
            }
        });
    };

    this.execute = function(model, method, paramsArrayByPosition, paramsDictByKey, onResponseOK) {
        $.xmlrpc({
            url: this.serverUrl + 'object',
            methodName: 'execute_kw',
            dataType: 'jsonrpc',
            params: [this.dbName, uid, this.pass, model, method, [paramsArrayByPosition], paramsDictByKey],
            success: function(response, status, jqXHR) {
                onResponseOK(response); // Returns method results
            },
            error: function(jqXHR, status, error) {
                alert('ERROR: ' + jqXHR + '-' + status + '-' + error);
            }
        });
    };

    this.search = function(model, domain, onResponseOK) {
        $.xmlrpc({
            url: this.serverUrl + 'object',
            methodName: 'execute',
            dataType: 'jsonrpc',
            params: [this.dbName, uid, this.pass, model, 'search', domain],
            success: function(response, status, jqXHR) {
                onResponseOK(response[0]); // Returns array with records ids
            },
            error: function(jqXHR, status, error) {
                alert('ERROR: ' + jqXHR + '-' + status + '-' + error);
            }
        });
    };

    this.search_count = function(model, domain, onResponseOK) {
        $.xmlrpc({
            url: this.serverUrl + 'object',
            methodName: 'execute',
            dataType: 'jsonrpc',
            params: [this.dbName, uid, this.pass, model, 'search_count', domain],
            success: function(response, status, jqXHR) {
                onResponseOK(response); // Returns number of records in supplied domain
            },
            error: function(jqXHR, status, error) {
                alert('ERROR: ' + jqXHR + '-' + status + '-' + error);
            }
        });
    };

    this.read = function(model, ids, fields, onResponseOK) {
        var idList = $.xmlrpc.force('array', ids);

        $.xmlrpc({
            url: this.serverUrl + 'object',
            methodName: 'execute',
            dataType: 'jsonrpc',
            params: [this.dbName, uid, this.pass, model, 'read', idList, fields],
            success: function(response, status, jqXHR) {
                onResponseOK(response[0]); // Returns array of objects with data requested
            },
            error: function(jqXHR, status, error) {
                alert('ERROR: ' + jqXHR + '-' + status + '-' + error);
            }
        });
    };

    this.fields_get = function(model, domain, fields_attrs, onResponseOK) {
        if (typeof fields_attrs === 'undefined') {
            fields_attrs = ['string', 'help', 'type'];
        };

        $.xmlrpc({
            url: this.serverUrl + 'object',
            methodName: 'execute',
            dataType: 'jsonrpc',
            params: [this.dbName, uid, this.pass, model, 'fields_get', domain, fields_attrs],
            success: function(response, status, jqXHR) {
                onResponseOK(response[0]); // Returns array of objects with fields definitions
            },
            error: function(jqXHR, status, error) {
                alert('ERROR: ' + jqXHR + '-' + status + '-' + error);
            }
        });
    };

    this.search_read = function(model, domain, options, onResponseOK) {
        $.xmlrpc({
            url: this.serverUrl + 'object',
            methodName: 'execute_kw',
            dataType: 'jsonrpc',
            params: [this.dbName, uid, this.pass, model, 'search_read', [domain], options],
            success: function(response, status, jqXHR) {
                onResponseOK(response[0]); // Returns array of objects with data requested
            },
            error: function(jqXHR, status, error) {
                alert('ERROR: ' + jqXHR + '-' + status + '-' + error);
            }
        });
    };

    this.create = function(model, data, onResponseOK) {
        $.xmlrpc({
            url: this.serverUrl + 'object',
            methodName: 'execute',
            dataType: 'jsonrpc',
            params: [this.dbName, uid, this.pass, model, 'create', data],
            success: function(response, status, jqXHR) {
                onResponseOK(response); // Returns id of created record
            },
            error: function(jqXHR, status, error) {
                alert('ERROR: ' + jqXHR + '-' + status + '-' + error);
            }
        });
    };

    this.write = function(model, id, data, onResponseOK) {
        // Data must be in dictionary format, object literals, for example:
        // {name: 'John Doe', country: 'au', ...}
        var id_and_data = [[id], $.xmlrpc.force('struct', data)];

        $.xmlrpc({
            url: this.serverUrl + 'object',
            methodName: 'execute',
            dataType: 'jsonrpc',
            params: [this.dbName, uid, this.pass, model, 'write', id_and_data],
            success: function(response, status, jqXHR) {
                onResponseOK(response); // Returns ¿?¿?¿?
            },
            error: function(jqXHR, status, error) {
                alert('ERROR: ' + jqXHR + '-' + status + '-' + error);
            }
        });
    };

    this.unlink = function(model, id, onResponseOK) {
        $.xmlrpc({
            url: this.serverUrl + 'object',
            methodName: 'execute',
            dataType: 'jsonrpc',
            params: [this.dbName, uid, this.pass, model, 'unlink', [[id]]],
            success: function(response, status, jqXHR) {
                onResponseOK(response); // Returns ¿?¿?¿?
            },
            error: function(jqXHR, status, error) {
                alert('ERROR: ' + jqXHR + '-' + status + '-' + error);
            }
        });
    };
};