
////////////////////////
// VARIABLES GLOBALES //
////////////////////////
var tablaProductos = null;
var panelUsuarios = null;
var idCategoriaProductosVendiblesPH = 0;


function tabla(objetivo) {
    /* "objetivo" es el objeto tabla devuelto por un selector de jQuery */
    var posicion = 0;
    var cuerpo = objetivo.children('tbody');

    this.subirTabla = function() {
        var alturaElemento = cuerpo.find('tr:first-child td:last-child').outerHeight();
        if (posicion >= alturaElemento)
            posicion -= alturaElemento;
        else {
            if (posicion == 0)
                objetivo.stop(true, true)
                        .animate({backgroundColor: '#FFB2B2'}, 100)
                        .animate({backgroundColor: 'transparent'}, 500);
            posicion = 0;
        }
        cuerpo.scrollTop(posicion);
    };

    this.bajarTabla = function() {
        var elementosEnTabla = cuerpo.children('tr').length;
        var alturaElemento = cuerpo.find('tr:first-child td:last-child').outerHeight();
        var alturaContenido = alturaElemento * elementosEnTabla;
        if (posicion + cuerpo.height() >= alturaContenido) {
            objetivo.stop(true, true)
                    .animate({backgroundColor: '#FFB2B2'}, 100)
                    .animate({backgroundColor: 'transparent'}, 500);
        } else {
            posicion += alturaElemento;
            cuerpo.scrollTop(posicion);
        }
    };

    // Capturamos evento de scroll con barra de desplazamiento, para actualizar variable "posicion"
    objetivo.children('tbody').scroll(function() {
        posicion = $(this).scrollTop();
    });
}

function usuarios(objetivo) {
    /* "objetivo" es el objeto div devuelto por un selector de jQuery */
    var posicion = 0;
    var alturaElemento = objetivo.find('button').outerHeight() + 10;

    this.arriba = function() {
        if (posicion >= alturaElemento)
            posicion -= alturaElemento;
        else {
            if (posicion == 0)
                objetivo.stop(true, true)
                        .animate({backgroundColor: '#FFB2B2'}, 100)
                        .animate({backgroundColor: 'transparent'}, 500);
            posicion = 0;
        }
        objetivo.scrollTop(posicion);
    };

    this.abajo = function() {
        var alturaContenido = objetivo[0].scrollHeight;
        if (posicion + objetivo.height() >= alturaContenido) {
            objetivo.stop(true, true)
                    .animate({backgroundColor: '#FFB2B2'}, 100)
                    .animate({backgroundColor: 'transparent'}, 500);
        } else {
            posicion += alturaElemento;
            objetivo.scrollTop(posicion);
        }
    };

    // Capturamos evento de scroll con barra de desplazamiento, para actualizar variable "posicion"
    objetivo.scroll(function() {
        posicion = $(this).scrollTop();
    });
}


$(document).ready(function () {
    $('#inputEAN').on('keyup', function(e) {
        var code = e.keyCode || e.which;
        if (code == 13) { // Fin de entrada de código
           buscarEAN();
        }
    }).focus();

    $('#inputProducto').on('change', function() {
        buscarProducto();
    }).on('click', function() {
        if (($(this).val() == '') && ($('#inputEAN').val() == ''))
            mostrarProductosVendibles();
    });

    $('span.iconoCombo').on('click', function() {
        if (
            ($(this).parents('div#producto').length > 0) &&
            ($('#inputProducto').val() == '') &&
            ($('#inputEAN').val() == '')
           )
            mostrarProductosVendibles();

        $(this).parents('div').first().find('div input').focus();
    });

    $('#inputLote').on('keydown', function(e) {
        // Sólo se permite seleccionar una opción del combo
        e.preventDefault();
    });

    $('#inputEAN, #inputProducto').keyboard({
        openOn: null,
		stayOpen: false,
        usePreview: false,
        autoAccept: true,
        hidden: function(event, keyboard, el) {
            setTimeout(function() {$(el).focus();}, 200);
        },
        enterNavigation: false,
        appendLocally: false,
		layout: 'ms-Spanish',
		css: {
			input: 'form-control input',
			container: 'center-block well',
			buttonDefault: 'btn btn-default',
			buttonHover: 'btn-primary',
			buttonAction: 'active',
			buttonDisabled: 'disabled'
		}
    });

    $('span.iconoTeclado').click(function(){
        var input = $(this).prev('div').children('input');
        var kb = input.getkeyboard();
        if (kb.isOpen) {
            kb.close();
        } else {
            kb.reveal();
            input.val('');
        }
    });

    // Eventos para gestionar las listas desplegables
    $('div.combo span.lista').on('mousedown vmousedown', 'span', function(e) {
        var lista = $(this).parent();
        var input = lista.parents('div').first().children('div').children('input');
        input.val($(this).text());
        lista.children('span').removeClass('activa');
        lista.data('id', $(this).data('id')); // Guardamos el id activo en la lista
        $(this).addClass('activa');
        lista.blur().change(); // Disparamos evento onchange
    });

    $('div#producto span.lista').change(function() {
        var ean = $(this).children('span.activa').data('ean');
        $('#inputEAN').val((ean) ? ean : '');
        comprobarLotes();
    });

    $('div#botonesCantidad').on('click', 'button', function() {
        $('#inputCantidad').focus();
    });

    $('#inputCantidad').on('keyup', function() {
        this.value = this.value.replace(/[^0-9]/g, '');
        this.value = parseInt(this.value);
        if (this.value == 'NaN')
            this.value = 0;

        comprobarLotes();
    });

    // Para evitar el autocompletado del navegador
    var aleatorio = Math.random();
    $('input').each(function(idx) {
        $(this).attr('name', aleatorio + idx);
    });

    tablaProductos = new tabla($('div#listaProductos table'));

    // Iniciamos sesión en Odoo y mostramos lista de usuarios
    odooObj.login(function() {
        seleccionarUsuario();
//        buscarIdCategVendibles();
    });
});

function limpiarFormulario() {
    $('#inputEAN').focus();
    $('div.combo span.lista').empty();
}

function mostrarMensaje(titulo, mensaje, callback, preguntar) {
    // Valores de parámetros por defecto
    callback = (callback == undefined) ? false : callback;
    preguntar = (preguntar == undefined) ? false : preguntar;

    mensaje = '<div id="mensaje" class="modal fade">' +
              '    <div class="modal-dialog">' +
              '        <div class="modal-content">' +
              '            <div class="modal-header">' +
              '                <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
              '                <h4 class="modal-title">' + titulo + '</h4>' +
              '            </div>' +
              '            <div class="modal-body">' +
              '                <p>' + mensaje + '</p>' +
              '            </div>' +
              '            <div class="modal-footer">';

    // Si preguntamos, mostramos opciones
    if (preguntar) {
        mensaje += '                <button type="button" class="btn btn-lg btn-default" data-dismiss="modal">Cancelar</button>' +
                   '                <button type="button" class="btn btn-lg btn-primary" data-dismiss="modal" onclick="' + callback + ';">Aceptar</button>';
    } else {
        mensaje += '                <button type="button" class="btn btn-lg btn-primary" data-dismiss="modal" onclick="' + callback + ';">Continuar</button>';
    }

    mensaje += '            </div>' +
               '        </div>' +
               '    </div>' +
               '</div>';

    $('body').append(mensaje);
    $('div#mensaje').modal().on('hidden.bs.modal', function (e) {
        $(this).remove();
    });
}

function buscarEAN() {
    var ean = $('#inputEAN').val().trim();
    if (ean.length > 10) {
        odooObj.search_read('product.product', [['ean13', 'like', ean]],
            {fields: ['name_template', 'ean13']},
            function(productos) {
                var lista = $('div#producto span.lista');
                lista.empty();
                $.each(productos, function(idx, obj) {
                    lista.append('<span data-id="' + obj.id + '" data-ean="' + obj.ean13 + '">' + obj.name_template + '</span>');
                });
                if (productos.length > 0) {
                    lista.children('span:first').addClass('activa');
                    $('#inputProducto').val(productos[0].name_template);
                } else
                    $('#inputProducto').val('');

                comprobarLotes();
            }
        );
    }
}

function buscarProducto(autoSeleccionar) {
    var txt = $('#inputProducto').val().trim();
    if (txt.length > 2) {
        odooObj.search_read('product.product',
            [
//                ['product_tmpl_id.categ_ids', '=', idCategoriaProductosVendiblesPH],
                ['product_tmpl_id.sale_ok', '=', true],
                ['name_template', 'ilike', txt]
            ],
            {fields: ['name_template', 'ean13']},
            function(productos) {
                var lista = $('div#producto span.lista');
                lista.empty();
                $.each(productos, function(idx, obj) {
                    lista.append('<span data-id="' + obj.id + '" data-ean="' + obj.ean13 + '">' + obj.name_template + '</span>');
                });
                if ((autoSeleccionar != undefined) && (autoSeleccionar == true)) {
                    $('#inputEAN').val(lista.children('span:first-child').addClass('activa').data('ean'));
                    comprobarLotes();
                }
            }
        );
    }
}

function mostrarProductosVendibles() {
    odooObj.search_read('product.product',
        [
//            ['product_tmpl_id.categ_ids', '=', idCategoriaProductosVendiblesPH]
            ['product_tmpl_id.sale_ok', '=', true]
        ],
        {fields: ['name_template', 'ean13'], order: 'name_template'},
        function(productos) {
            var lista = $('div#producto span.lista');
            lista.empty();

            $.each(productos, function(idx, obj) {
                lista.append('<span data-id="' + obj.id + '" data-ean="' + obj.ean13 + '">' + obj.name_template + '</span>');
            });
        }
    );
}

function ajustaCantidad(variacion) {
    var campo = $('#inputCantidad');
    var cantidad = parseInt(campo.val());

    if (isNaN(cantidad) || (variacion == 0))
        cantidad = 0 + variacion;
    else
        cantidad = cantidad + variacion;

    campo.val((cantidad > -1) ? cantidad : 0);

    comprobarLotes();
}

function comprobarLotes() {
    var location_id = $('span#usuario').data('location_id');
    var product_id  = $('div#producto span.lista span.activa').data('id');
    var qty         = $('#inputCantidad').val();

    odooObj.search_read('stock.quant', [
            ['lot_id.product_id', '=', product_id],
            ['location_id.location_id', '=', location_id], // Ubicación de almacén padre
            ['reservation_id', '=', false],
            ['qty', '>=', qty]
        ], {fields: ['lot_id'], order: 'lot_id'}, function (lotes) {
            var lista = $('div#lote span.lista');
            var idActivo = lista.data('id');
            lista.empty();
            $.each(lotes, function(idx, obj) {
                lista.append('<span data-id="' + obj.lot_id[0] + '">' + obj.lot_id[1] + '</span>');
            });
            if (lotes.length > 0) {
                var lote = lista.children('span[data-id="' + idActivo + '"]');
                if ((idActivo > 0) && (lote.length > 0)) {
                    lote.addClass('activa');
                    $('#inputLote').val(lote.text());
                } else {
                    lista.children('span:first').addClass('activa');
                    $('#inputLote').val(lotes[0].lot_id[1]);
                }
            } else
                $('#inputLote').val('');
        }
    );
}

function editarProducto(detail_id) {
    var registros = $('div#listaProductos table tbody tr[data-detail_id="' + detail_id + '"] td');
    var listaProductos = $('div#producto span.lista');
    $('div#formulario').css('z-index', 1001);
    $('div#capaSombra').show();
    $('button#btnLimpiar').hide();
    $('form').trigger('reset');
    limpiarFormulario();
    $('#inputProducto').val($(registros[0]).text());
    $('#inputCantidad').val($(registros[2]).text());
    buscarProducto(true);
    eliminarProducto(detail_id);
}

function borrarProducto(detail_id) {
    mostrarMensaje('CONFIRMAR BORRADO', '¿Quiere anular la baja de este producto?', 'eliminarProducto(' + detail_id + ')');
}

function eliminarProducto(detail_id) {
    odooObj.execute('product.drop.details', 'unreserve_detail_id', detail_id, {}, function(res) {
        if (res[0] == true) {
            $('div#listaProductos table tbody tr[data-detail_id="' + detail_id + '"]').remove();
        } else
            mostrarMensaje('ERROR', 'NO SE HA PODIDO DESHACER LA RESERVA DE ESTE PRODUCTO.');
    });
}

function reservarProducto() {
    function guardarReserva(drop_id) {
        // Reservamos el producto del lote y la cantidad especificados
        odooObj.create('product.drop.details', {
                name: product_id,
                product_qty: product_qty,
                lot_id: lot_id,
                drop_id: drop_id
            }, function(res) {
                detail_id = res[0];

                // Agregamos el nuevo elemento a la lista de productos reservados
                nuevoElem = '<tr data-detail_id="' + detail_id + '">' +
                    '    <td class="col-xs-6">' + $('#inputProducto').val() + '</td>' +
                    '    <td class="col-xs-2">' + $('#inputLote').val() + '</td>' +
                    '    <td class="col-xs-1">' + product_qty + '</td>' +
                    '    <td class="col-xs-3">' +
                    '        <button type="button" class="btn btn-lg btn-primary" onclick="editarProducto(' + detail_id + ');">' +
                    '            <span style="padding: 0 10px;" class="glyphicon glyphicon-pencil" aria-hidden="true"></span>' +
                    '        </button>' +
                    '        <button type="button" class="btn btn-lg btn-danger" onclick="borrarProducto(' + detail_id + ');">' +
                    '            <span style="padding: 0 10px;" class="glyphicon glyphicon-trash" aria-hidden="true"></span>' +
                    '        </button>' +
                    '    </td>' +
                    '</tr>';
                $('div#listaProductos table tbody').prepend(nuevoElem);

                // Limpiamos el formulario parcialmente
                $('#inputCantidad').val('');
                $('#inputLote').val('');
                comprobarLotes();

                // Ocultamos capa de edición y volvemos al modo normal
                $('div#capaSombra').hide();
                $('div#formulario').css('z-index', 999);
                $('button#btnLimpiar').show();
            }
        );
    }

    var uid = $('span#usuario').data('uid');
    var drop_id = $('form').data('drop_id');
    var product_id = $('div#producto span.lista span.activa').data('id');
    var product_qty =  $('#inputCantidad').val();
    var lot_id =  $('div#lote span.lista span.activa').data('id');
    var detail_id = 0;
    var nuevoElem = '';

    // Validamos el formulario
    if (!(product_id > 0)) {
        mostrarMensaje('ATENCIÓN', 'No se ha seleccionado ningún producto.');
        return;
    }

    if (!(product_qty > 0)) {
        mostrarMensaje('ATENCIÓN', 'Debe especificar una cantidad a dar de baja mayor que cero.');
        return;
    }

    if (!(lot_id)) {
        mostrarMensaje('ATENCIÓN', 'No se ha seleccionado ningún lote de origen.');
        return;
    }

    // Creamos el grupo de baja de productos si no existe ya y reservamos
    if (drop_id == 0) {
        odooObj.execute('product.drop', 'xmlrpc_create', uid, {}, function(res) {
            drop_id = res[0];
            $('form').data('drop_id', drop_id);
            guardarReserva(drop_id);
        });
    } else
        guardarReserva(drop_id);
}

function confirmarBaja() {
    if ($('div#listaProductos table tbody').children().length == 0) {
        mostrarMensaje('ERROR', 'No ha especificado productos para dar de baja.');
        return;
    }

    mostrarMensaje('CONFIRMAR BAJA',
                   'Se van a dar de baja todos los productos indicados en la lista inferior.<br>¿Desea continuar con la operación?',
                   'bajaProductos()', true);
}

function bajaProductos() {
    var drop_id = $('form').data('drop_id');

    odooObj.execute('product.drop', 'confirm_drop_id', drop_id, {}, function(res) {
        if (res[0] == true) {
            $('form').trigger('reset').data('drop_id', 0);
            limpiarFormulario();
            $('div#listaProductos table tbody').empty();
            setTimeout(function() { // Para que le dé tiempo a finalizar a la animación del diálogo anterior
                mostrarMensaje('RESULTADO DE LA OPERACIÓN', 'OK: PRODUCTOS DADOS DE BAJA CORRECTAMENTE.', 'window.location.reload(true)');
            }, 1000);
        } else
            setTimeout(function() { // Para que le dé tiempo a finalizar a la animación del diálogo anterior
                mostrarMensaje('RESULTADO DE LA OPERACIÓN', 'ERROR: NO SE HA PODIDO CONFIRMAR LA BAJA DE ESTOS PRODUCTOS.');
            }, 1000);
    });
}

function activarPanelUsuarios(selector) {
    panelUsuarios = new usuarios(selector);
}

function activarUsuario(partner_id, uid, company_id, nombre, imagen) {
    $('form, div#listaProductos').show();
    $('div#ventanaUsuarios').fadeOut(function() {$(this).hide();});
    $('h2#titulo').html('Baja de artículos para uso interno');
    $('span#usuario').data('partner_id', partner_id)
                     .data('uid', uid)
                     .data('company_id', company_id)
                     .html(nombre);
    $('a#btnSalir').show();
    $('img#foto').attr('src', imagen).show();
    $('div#selectorUsuarios').off().empty();

    // listo para empezar
    limpiarFormulario();

    // En diferido, buscamos el almacén principal de la empresa del usuario
/*
    odooObj.search_read('stock.warehouse', [['company_id', '=', company_id]], {fields: ['lot_stock_id']},
        function(ubicacion) {
            $('span#usuario').data('location_id', ubicacion[0].lot_stock_id[0]);
        }
    );
*/
    $('span#usuario').data('location_id', 22); // Physical Locations / CY01 / Existencias / Producto terminado
}

function seleccionarUsuario() {
    odooObj.search_read('res.users', [], {fields: ['partner_id', 'company_id']},
        function(usuarios) {
            var ids = [];
            $.each(usuarios, function(idx, obj) {
                ids.push(obj.partner_id[0]);
            });

            odooObj.search_read('res.partner', [['id', 'in', ids]], {fields: ['display_name', 'image_medium']},
                function(datos) {
                    var selector = $('div#selectorUsuarios');
                    $.each(datos, function(idx, obj) {
                        var uid = -1;
                        var company_id = -1;
                        $.each(usuarios, function(userIdx, userObj) {
                            if (userObj.partner_id[0] == obj.id) {
                                uid = userObj.id;
                                company_id = userObj.company_id[0];
                            };
                        });
                        selector.append('<button class="btn btn-default" data-partner_id="' + obj.id +
                            '" data-uid="' + uid + '" + data-company_id="' + company_id + '">' +
                            '<img src="data:image/jpg;base64,' + obj.image_medium + '"/>' +
                            '<div><p>' + obj.display_name + '</p></div></button>');
                    });

                    activarPanelUsuarios(selector);

                    selector.on('click', 'button', function() {
                        with ($(this)) {
                            activarUsuario(
                                data('partner_id'),
                                data('uid'),
                                data('company_id'),
                                find('p').text(),
                                find('img').attr('src')
                            );
                        };
                    });
                }
            );
        }
    );
}

function buscarIdCategVendibles() {
    // Localizamos el id de la categoría de productos fabricados por Pharmadus que se pueden vender
    odooObj.search_read('ir.model.data',
        [['name', 'ilike', 'prodcat084']],
        {fields: ['res_id']},
        function(res) {
            idCategoriaProductosVendiblesPH = res[0].res_id;
        }
    );
}