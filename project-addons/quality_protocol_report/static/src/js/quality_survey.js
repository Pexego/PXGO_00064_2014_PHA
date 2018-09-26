$(document).ready(function(){
    'use strict';
    $("#send_form").click(send_form_server);
    // Si el div #exist existe se rellenan las preguntas por ajax.
    if ($("#exist").length != 0) {
        $("#all_data #survey :input").attr("disabled", true);
        //$("#send_form").hide();
        fill_data();
    }

if (typeof String.prototype.startsWith != 'function') {
    // see below for better implementation!
    String.prototype.startsWith = function (str){ return this.indexOf(str) == 0; };
}
if (typeof String.prototype.contains != 'function') {
    String.prototype.contains = function(it){ return this.indexOf(it) != -1; };
}
});

var JQUERY_UI_TYPES = {
    'char': 'text',
    'selection': 'select',
    'boolean': 'checkbox',
    'date': 'ui-datepicker',
    'datetime': 'datetime-local',
    'integer': 'number',
    'float': 'number',
    'many2one': 'text'
};

var to_remove_rows = [];

function check_name(event, fill_field){
    var context = {lang: 'es_ES', tz: 'Europe/Madrid'};
    var element_id = event.target.id;
    var table = $('#'.concat(element_id)).closest('table');
    var row = $('#'.concat(element_id)).closest('tr');
    var insert_to_table = false;
    if(typeof table.attr('insert_to_table') !== typeof undefined && table.attr('insert_to_table') !== false){
        insert_to_table = table.attr('insert_to_table');
    }
    var text = event.target.value;
    var tablename = element_id.substring(0, element_id.indexOf('_'))
    var element_index = element_id.substring(element_id.lastIndexOf('_'))
    var fill_id = tablename.concat('_').concat(fill_field).concat(element_index)
    var field_name = event.target.getAttribute('name');
    field_name = field_name.substring(field_name.indexOf('_')+1, field_name.lastIndexOf('_'))
    var fill_value = ''
    if (text.length !== 0){
        var model = event.target.getAttribute('model');
        if (typeof model !== typeof undefined && model !== false){
            var obj = new openerp.web.Model(model, context);
            obj.call('search', [[['name', '=', text]]]).then(function(result) {
                if(result.length === 0){
                    event.target.style.backgroundColor = "red";
                    $('input#'.concat(fill_id)).val('');
                }
                else{
                    event.target.setAttribute('quality_protocol_value', result);
                    event.target.style.backgroundColor = "transparent";
                    if(fill_field != ''){
                        obj.query([fill_field]).filter([['id', 'in', result]]).context(context).all().then(function(result){
                            fill_value = result[0][fill_field][1];
                            $('input#'.concat(fill_id)).val(fill_value);
                            //Se hace dentro de la funcion para esperar por el resultado
                            if(insert_to_table !== false){
                                var row_id = row.find('input[id^='.concat(tablename).concat('_id]')).val();
                                var same_id = $('input[id^='.concat(insert_to_table).concat('_id][value='.concat(row_id).concat(']')))
                                //Si no existe en la otra tabla una fila con el mismo id se crea
                                if(!same_id.length){
                                    var row_dict = {id: row_id}
                                    row_dict[field_name] = text;
                                    row_dict[fill_field] = fill_value;
                                    $('table[id=' + insert_to_table + ']').appendGrid('appendRow', [row_dict]);
                                }
                                else{
                                    //Se actualizan los datos de la otra fila
                                    var same_tr = same_id.closest('tr');
                                    same_tr.find('input[id^=' + insert_to_table + '_' + field_name + ']').val(text)
                                    if(fill_field != ''){
                                        same_tr.find('input[id^=' + insert_to_table + '_' + fill_field + ']').val(fill_value)
                                    }
                                }
                            }
                        });
                    }

                }
            });
        }
    }
    else{
        event.target.style.backgroundColor = "transparent";
    }
}

function isDateTime(date) {
    try
    {
        if ((date.length == 19 || date.length == 16) && isNaN(date)) {
            //check if date is a valid date by using Date.prase();
            //datetocheck is string 'YYYY-MM-DDThh:mm(:ss)'
            var year = +date.substring(0,4);
            var month = +date.substring(5,7);
            var day = +date.substring(8,10);
            var hour = +date.substring(11,13);
            var minute = +date.substring(14,16);
            if (date.length == 19) {
                var second = +date.substring(17,19);
                if(isNaN(second)) return false;
            }
            else {
                var second = "00";
            }

            if(isNaN(month)) return false;
            if(isNaN(day)) return false;
            if(isNaN(year)) return false;
            if(isNaN(hour)) return false;
            if(isNaN(minute)) return false;

            datetocheck = Date(year, month, day, hour, minute, second, 0);
            Date.parse(datetocheck);
            return true;
        }
        else {
            return false;
        }
    }
    catch(err)
    {
        return false;
    }
};

function isDate(date) {
    try
    {
        if (date.length == 10 && isNaN(date)) {
            //check if date is a valid date by using Date.prase();
            //datetocheck is string 'YYYY-MM-DDThh:mm(:ss)'
            var month = +date.substring(0,2);
            var day = +date.substring(3,5);
            var year = +date.substring(6,10);

            if(isNaN(month)) return false;
            if(isNaN(day)) return false;
            if(isNaN(year)) return false;

            datetocheck = Date(year, month, day, 0, 0, 0, 0);
            Date.parse(datetocheck);
            return true;
        }
        else {
            return false;
        }

    }
    catch(err)
    {
        return false;
    }
};

function datetimeToISOStr(date) {
            var day = date.getDate();
            var month = date.getMonth() + 1;
            var year = date.getFullYear();
            var hours = date.getHours();
            var minutes = date.getMinutes();
            var seconds = date.getSeconds();
            if (month < 10) month = "0" + month;
            if (day < 10) day = "0" + day;
            if (hours < 10) hours = "0" + hours;
            if (minutes < 10) minutes = "0" + minutes;
            if (seconds < 10) seconds = "0" + seconds;

            var today = year + "-" + month + "-" + day + "T" + hours + ":" + minutes + ":" + seconds;
            return today;
};

function desmarcaCampoSiNo(obj) {
    if (obj.data('marcado')) {
        if (obj.attr('value') == 'Sí') {
            var valor = 'No';
        } else {
            var valor = 'Sí';
        };
        obj.data('marcado', false);
        $('input#' + obj.attr('id') + '[value="' + valor + '"]').prop('checked', true);
    } else {
        obj.data('marcado', true);
    };
};

function plantillaSiNo(obj) {
    var valor = obj.val();

    obj.after(
        '<div class="contenedor_si_no">' +
        '<label class="campo_si_no">' +
        '  Sí<input class="form-control" style="display: inline;" name="' +
        obj.attr('name') + '" value="Sí" type="radio"/>' +
        '  <span class="campo_si_no_indicador"></span>' +
        '</label>' +
        '<label class="campo_si_no">' +
        '  No<input class="form-control" style="display: inline;" name="' +
        obj.attr('name') + '" value="No" type="radio"/>' +
        '  <span class="campo_si_no_indicador"></span>' +
        '</label>' +
        '</div>'
    );

    var id = obj.attr('id');

    objSi = $('input[name="' + obj.attr('name') + '"][value="Sí"]');
    objSi.prop('checked', obj.val() == 'Sí').data('marcado', obj.val() == 'Sí');
    if (id !== null) {objSi.prop('id', id)};

    objNo = $('input[name="' + obj.attr('name') + '"][value="No"]');
    objNo.prop('checked', obj.val() == 'No').data('marcado', obj.val() == 'No');
    if (id !== null) {objNo.prop('id', id)};

    if (obj.tipo == 'No') {
        objSi.parent().hide();
        objNo.click(function() {desmarcaCampoSiNo($(this))});
    };
    if (obj.tipo == 'Sí') {
        objNo.parent().hide();
        objSi.click(function() {desmarcaCampoSiNo($(this))});
    };

    obj.remove();
};

function preparaSiNo() {
    var inputsSN = $('input[name*="_box_sn"]');
    if (inputsSN.length > 0) {
        inputsSN.each(function() {
            var obj = $(this);
            obj.tipo = 'SíNo';
            plantillaSiNo(obj);
        });
    };
    var inputsSI = $('input[name*="_box_si"]');
    if (inputsSI.length > 0) {
        inputsSI.each(function() {
            var obj = $(this);
            obj.tipo = 'Sí';
            plantillaSiNo(obj);
        });
    };
    var inputsNO = $('input[name*="_box_no"]');
    if (inputsNO.length > 0) {
        inputsNO.each(function() {
            var obj = $(this);
            obj.tipo = 'No';
            plantillaSiNo(obj);
        });
    };
};

function preparaTime() {
    var inputsTime = $('input[name*="_time"]');
    if (inputsTime.length > 0) {
        inputsTime.each(function() {
            $(this).prop('type', 'time');
        });
    };
};

$(function () {
//    if($("#done").length) {
//        $(":input").prop('disabled', true);
//    }
    $("#bodyaccord").hide();
    $("#headeraccord").click(function(){
       if($("#bodyaccord").is(":visible")){
            $("#bodyaccord").hide();
       }
       else{
           $("#bodyaccord").show();
       }
    });
    $('<div style="clear: both;"/>').insertAfter( ".unique_field" );
    $('#all_data').find('.quality_form').each(function() {
        var record = Number($(this).attr("record"));
        var model = $(this).attr("model");
        var context = {lang: 'es_ES', tz: 'Europe/Madrid'};
        $(this).find('.quality_field').each(function() {
            var field_to_represent = $(this).attr("qfield");
            var filter = $(this).attr("filter") ? JSON.parse($(this).attr("filter")) : [];
            var filter_model = $(this).attr("filter-model")
            var columns = $(this).attr("columns").split(",");
            var columns_options = $(this).attr("columns-options") ? eval('(' + $(this).attr("columns-options") + ')') : {};
            //Se establece que en ciertas columnas al insertar nuevas mediante el boton no se aplique alguna opcion.
            var columns_no_insert_options = $(this).attr("no-insert-options") ? eval('(' + $(this).attr("no-insert-options") + ')') : {};
            var extra_attrs = $(this).attr("extra_attrs") ? eval('(' + $(this).attr("extra_attrs") + ')') : {};
            var columns_widths = $(this).attr("columns-widths") ? $(this).attr("columns-widths").split(',') : [];
            var no_delete_option = $(this).attr("nodelete") ? $(this).attr("nodelete") : false;
            var no_insert_option = $(this).attr("noinsert")  ? $(this).attr("noinsert") : false;
            var init_rows = $(this).attr("initrows")  ? $(this).attr("initrows") : 5;
            var self = $(this);
            var obj = new openerp.web.Model(model, context);
            /* Se rellena la tabla con las propiedades de cada columna*/
            obj.call("fields_get", [field_to_represent], {context: context}).then(function(field_data) {
                var view_model = new openerp.web.Model(field_data[field_to_represent].relation, context);
                var table_columns = [];
                var format_columns = {};
                view_model.call("fields_get", [columns], {context: context}).then(function(fields) {
                    for (var i = 0; i<columns.length; i++) {
                        var key = columns[i];
                        if (key === "id") {
                            table_columns.push({name: key, type: 'hidden'});
                        } else {
                            if (columns_options && columns_options[key] == "hidden") {
                                table_columns.push({name: key, type: 'hidden', ctrlProp:{'disabled': true}});
                            } else {
                                var ctrlProp = {};
                                var displayCss = {};
                                var uiOption = {};
                                var extraAttrs = {};
                                if (fields[key].required) {
                                    ctrlProp['required'] = true;
                                }
                                if (columns_no_insert_options && columns_no_insert_options[key] == "disabled") {
                                    ctrlProp['insert_no_disabled'] = true;
                                }

                                if (extra_attrs && extra_attrs[key]) {
                                    for(Exkey in extra_attrs[key]){
                                        extraAttrs[Exkey] = extra_attrs[key][Exkey]
                                    }
                                }
                                if (columns_options && columns_options[key] == "disabled"/* || $("#done").length */) {
                                    ctrlProp['disabled'] = true;
                                }
                                if (columns_widths.length > 0) {
                                    displayCss['width'] = columns_widths[i];
                                }
                                format_columns[key] = fields[key].type;

                                if (JQUERY_UI_TYPES[fields[key].type] == "ui-datepicker") {
                                    uiOption['dateFormat'] = 'dd/mm/yy'
                                }

                                table_columns.push({name: key, display: fields[key].string, type: JQUERY_UI_TYPES[fields[key].type], ctrlProp: ctrlProp, displayCss: displayCss, uiOption: uiOption, extraAttrs: extraAttrs});
                            }

                        }
                    }
                    /*Se rellena la tabla con los datos de los registros*/
                    obj.call('read', [record, [field_to_represent]], {context: context}).then(function(response) {
                        var tablaAG = false;
                        if (response[field_to_represent].length > 0) {
                            var initData = [];
                            var read_filter = filter.concat([['id', 'in', response[field_to_represent]]]);
                            view_model.call('search_read', [read_filter, columns], {context: context}).then(function(rows_data) {
                                for (var j = 0; j<rows_data.length;j++) {
                                    var gridRow = {};
                                    for (var k=0; k<columns.length; k++) {
                                        if (format_columns[columns[k]] === "datetime") {
                                            gridRow[columns[k]] = rows_data[j][columns[k]] ? datetimeToISOStr(openerp.str_to_datetime(rows_data[j][columns[k]])) : '';
                                        }
                                        else if (format_columns[columns[k]] === "date") {
                                            gridRow[columns[k]] = rows_data[j][columns[k]] ? openerp.str_to_date(rows_data[j][columns[k]]).format("d/m/Y") : '';
                                        }
                                        else if (format_columns[columns[k]] === "many2one") {
                                            gridRow[columns[k]] = rows_data[j][columns[k]] ? rows_data[j][columns[k]][1] : '';
                                        }
                                        else {
                                            gridRow[columns[k]] = rows_data[j][columns[k]] ? rows_data[j][columns[k]] : '';
                                        }
                                    }
                                    initData.push(gridRow);
                                }
                                self.appendGrid({
                                    initRows: init_rows,
                                    columns: table_columns,
                                    hideButtons: {
                                        removeLast: true,
                                        remove: true,
                                        moveUp: true,
                                        moveDown: true,
                                        insert: true,
                                        append: no_insert_option
                                    },
                                    hideRowNumColumn: true,
                                    initData: initData,
                                    customGridButtons:{
                                                append: $('<button/>').text('Insert').get(0),
                                            },
                                    customRowButtons: no_delete_option ? [] : [{
                                        uiButton: {icons: {primary: 'ui-icon-delete'}, text: false },
                                        click: deleteRow,
                                        btnCss: {'min-width': '20px'},
                                        btnAttr: {title: 'Remove row'},
                                        atTheFront: true
                                    },]
                                });
                            });
                        } else {
                            self.appendGrid({
                                initRows: init_rows,
                                columns: table_columns,
                                hideButtons: {
                                    removeLast: true,
                                    moveUp: true,
                                    remove: true,
                                    moveDown: true,
                                    insert: true,
                                    append: no_insert_option
                                },
                                hideRowNumColumn: true,
                                customGridButtons:{
                                    append: $('<button/>').text('Insert').get(0),
                                },
                                customRowButtons: no_delete_option ? [] : [{
                                    uiButton: {icons: {primary: 'ui-icon-delete'}, text: false},
                                    click: deleteRow,
                                    btnCss: {'min-width': '20px'},
                                    btnAttr: {title: 'Remove row'},
                                    atTheFront: true
                                },]
                            });
                        };
                    });
                });
            });
        });
    });

    setTimeout(function() {
        // Buscamos los campos con sufijo "_box_sino" para reemplazar
        // su input por dos botones de radio con ambas opciones
        preparaSiNo();

        // Buscamos los campos con sufijo "_time" para poner el tipo correcto
        // a su input y que aplique la máscara correcta para estos campos.
        preparaTime();

        // Los inputs de con botones de flecha no se muestran bien al imprimir
        // con phantomjs, así que les cambiamos el tipo a texto y pista...
        if (/Phantom.js bot/.test(window.navigator.userAgent)) {
            $('.quality_row input[type="date"]').each(function() {
                fecha = $(this).val();
                if (fecha.trim().length == 10) {  // isDate() no funciona bien aquí
                    fecha = openerp.str_to_date(fecha).format("d/m/Y");
                    $(this).prop('type', 'text').val(fecha);
                } else {
                    $(this).prop('type', 'text');
                };
            });

            $('.quality_row input[type="number"], ' +
              '.quality_row input[type="time"], ' +
              '.quality_row input[type="datetime-local"]').each(
                function() {
                    $(this).prop('type', 'text');
                }
            );
            $('div#realized_by').hide();
        };
    }, 1000);
});

//Falta pepararlo para multiples tablas
function deleteRow(evtObj, uniqueIndex, rowData) {
    if (rowData.id) {
        to_remove_rows.push(Number(rowData.id));
    }
    $('#tblAppendGrid').appendGrid('removeRow', uniqueIndex-1);
};

function fill_data() {
    $('#all_data').find('.survey').each(function() {
        var url_fill = $(this).attr("fill");
        $(this).find("form").each(function() {
            var the_form = $(this);
            $.ajax(url_fill, {
                    dataType: "json"
                })
                .done(function(json_data) {
                    _.each(json_data, function(value, key) {
                        the_form.find(".form-control[name=" + key + "]").val(value);
                        the_form.find("input[name^=" + key + "]").each(function() {
                            $(this).val(value);
                        });
                    });
                })
                .fail(function() {
                    console.warn("[survey] Unable to load prefill data");
                });
        });
    });
}

function write_server(write_vals, keys){
    var key = keys.pop()
    var record = key.split(",");
    var context = {lang: 'es_ES', tz: 'Europe/Madrid'};
    var obj = new openerp.web.Model(record[0], context);
    obj.call("write", [Number(record[1]), write_vals[key]], {context: context}).then(function(result){
        if(keys.length > 0){
            write_server(write_vals, keys);
        }
        else{
            window.location.replace($("#all_data").attr("url-submit"));
        }
    });
}

/*se envia los datos de las diferentes encuestas al servidor(funcion en controller de survey).
  Se hace una llamada por encuesta y página.
  Luego se llama a una función del modulo para que relacione el numero de serie con las respuestas.
*/
function send_form_server() {
    $('.js_errzone').html("").hide();
    $('#all_data').find('.survey').each(function() {
        var url_submit = $(this).attr("url-submit");
        var dat = $(this).find("form").serialize();
        // Si se cambia a disabled antes de serializar falla
        $(this).find(":input").attr("disabled", true);
        $("#send_form").hide();
        $(this).find("form").each(function() {

            $.ajax({
                url: url_submit,
                type: 'POST', // submission type
                data: dat,
                dataType: 'json', // answer expected type
                beforeSubmit: function() { // hide previous errmsg before resubmitting
                    $('.js_errzone').html("").hide();
                },
                success: function(response, status, xhr, wfe) { // submission attempt
                    if (_.has(response, 'errors')) { // some questions have errors
                        $("#all_data #survey :input").attr("disabled", false);
                        $("#send_form").show();
                        _.each(_.keys(response.errors), function(key) {
                            $("#" + key + '>.js_errzone').append('<p>' + response.errors[key] + '</p>').show();
                        });
                    } else if (_.has(response, 'redirect')) {
                        //No se tienen en cuenta los mensajes de redireccion.
                    } else { // server sends bad data
                        console.error("Incorrect answer sent by server");
                        $("#all_data :input").attr("disabled", false);
                        $("#send_form").show();
                    }
                },
                timeout: 5000,
                error: function(jqXHR, textStatus, errorThrown) { // failure of AJAX request
                    $('#AJAXErrorModal').modal('show');
                    $("#all_data :input").attr("disabled", false);
                    $("#send_form").show();
                }
            });
        });

    });
    /*
     * Se recorren todos los formularios añadiendo los datos a un diccionario
     * para hacer una única llamada para escribir los valores.
     * {'modelo,id': {'campo1': valor1, 'campo2o2m':[(1,id,{}),...]}}
     */
    var write_vals = {};
    $('#all_data').find('.view').each(function() {
        if ($(this).find("form").length) {
            $(this).find("form").each(function(){
                var base_model = $(this).attr("model");
                var base_record = Number($(this).attr("record"));
                var dat = decodeURIComponent($(this).serialize());
                index = base_model + ',' + base_record
                if (!(index in write_vals)) {
                    write_vals[index] = {};
                }
                //Se recorren las tablas con los datos de campos one2many
                $(this).find(".quality_field").each(function() {
                    var form_field = $(this).attr("qfield");
                    var columns_default = $(this).attr("columns-default") ? eval('(' + $(this).attr("columns-default") + ')') : {};
                    if(!(form_field in write_vals[index])){
                        write_vals[index][form_field] = []
                    }

                    var compare = $(this).attr("compare");
                    if(compare){
                        compare = compare.split(",");
                    }
                    var table_id = $(this).attr("id");
                    var records = {};
                    var elements = dat.split('&');
                    for (var i = 0; i< elements.length; i++) {
                        elements[i] = elements[i].replace(/\+/g, ' ')
                        if (!elements[i].startsWith(table_id)){
                            continue;
                        }
                        if (elements[i].contains("rowOrder")) {
                            continue;
                        }
                        var vals = elements[i].split('=');
                        var def = vals[0].split("_");
                        var row_index = def.pop();
                        var elem_id = def[0];
                        var field_name = def.join("_").replace(elem_id + "_", "");
                        //Se busca el campo para comparar valores.
                        if (row_index in records) {
                            records[row_index][field_name] = vals[1];
                        }
                        else {
                            records[row_index] = {};
                            records[row_index][field_name] = vals[1];
                        }
                        if(columns_default.hasOwnProperty(field_name)){
                            records[row_index][field_name] = columns_default[field_name];
                        }
                        if(compare && compare.length && field_name == compare[0]){
                            var compare_name = table_id + '_' + compare[1] + '_' + row_index;
                            if($("input[name='" + compare_name + "']").length){
                                var to_compare_val = $("input[name='" + compare_name + "']").val();
                                if(vals[1] != to_compare_val){
                                    alert(field_name + ', ' + compare[1]);
                                    throw new Error("Something went badly wrong!");
                                }
                            }
                        }
                    };
                    var to_delete_rows = []
                    for (var row in records) {
                        var empty = true;
                        for (var column in records[row]) {
                            if (records[row][column] != "") {
                                empty = false;
                            }
                            else {
                                records[row][column] = null;
                            }
                        }
                        if (empty) {
                            to_delete_rows.push(row);
                        }
                    }

                    for (var i = 0; i <  to_delete_rows.length; i++) {
                        delete records[to_delete_rows[i]];
                    }

                    if (to_remove_rows.length != 0) {
                        var fields = {};
                        for (var i=0;i<to_remove_rows.length;i++) {
                            write_vals[index][form_field].push([2, to_remove_rows[i]]);
                        }
                        to_remove_rows = [];
                    }

                    for (var row in records) {
                        for (var column in records[row]) {
                            if (isDateTime(records[row][column]) === true) {
                                records[row][column] = openerp.web.datetime_to_str(Date.parse(records[row][column]));
                            }
                            else if (isDate(records[row][column]) === true) {
                                records[row][column] = openerp.web.date_to_str(Date.parseExact(records[row][column], "d/M/yyyy"));
                            }
                        }

                        var fields = {};
                        if (records[row].id) {
                            var update_id = records[row].id;
                            delete records[row].id;
                            var finded = false;
                            for(var arr_index = 0; arr_index < write_vals[index][form_field].length; arr_index++){
                                if(write_vals[index][form_field][arr_index][0] == 1 && write_vals[index][form_field][arr_index][1] == update_id){
                                    write_vals[index][form_field][arr_index][2] = $.extend(write_vals[index][form_field][arr_index][2],records[row]);
                                    finded = true;
                                }
                            }
                            if(!finded){
                                write_vals[index][form_field].push([1, update_id, records[row]]);
                            }
                        }
                        else {
                            delete records[row].id;
                            write_vals[index][form_field].push([0, 0, records[row]]);
                        }
                    }
                });
                $(this).find(".form-control").each(function() {
                    if ($(this).attr('type') == 'radio') {
                        if ($(this).prop('checked')) {
                            var input_value = $(this).attr('value');
                            var name = $(this).attr('name');
                            if (['true', 'True', 'false', 'False'].indexOf(input_value) != -1) {
                                write_vals[index][name] = eval(input_value);
                            } else {
                                write_vals[index][name] = input_value;
                            }
                        }
                    } else {
                        var input_value = $(this).attr('value');
                        var name = $(this).attr('name');
                        if (input_value == '') {
                            input_value = null;
                        } else if ($(this).attr('type') == 'float') {
                            input_value = input_value.replace(',', '.');
                        }
                        if (name in write_vals[index]) {
                            alert('Se sobreescribe el valor del input ' + name);
                            throw new Error('Something went badly wrong!');
                        }
                        write_vals[index][name] = input_value;
                    };
                });
            });
        }
    });
    //Se recorre el diccionario, y se llama a write con los cambios.
    var keys = []
    for (var key in write_vals) {
        $.each(write_vals[key], function(index, value) {
            if (value instanceof Array) {
                value.forEach(function(entry){
                    if(entry[0] == 1 && String(entry[1]).search('NEW') != -1){
                        entry[0] = 0;
                        entry[1] = 0;
                    }
                    else if(entry[0] == 1){
                        entry[1] = Number(entry[1])
                    }
                });
            }
        });

        keys.push(key)
    }
    if(keys.length > 0){
        write_server(write_vals, keys);
    }
    else{
        window.location.replace($("#all_data").attr("url-submit"));
    }
}

    var jqVal = $.fn.val;
    var rreturn = /\r/g;
    $.fn.val = function( value ) {
        var hooks, ret, isFunction,
            elem = this[0];
        if ( !arguments.length ) {
            if ( elem ) {
                hooks = jQuery.valHooks[ elem.type ] || jQuery.valHooks[ elem.nodeName.toLowerCase() ];

                if ( hooks && "get" in hooks && (ret = hooks.get( elem, "value" )) !== undefined ) {
                    return ret;
                }
                var quality_protocol_value = this.attr('quality_protocol_value');
                if (typeof quality_protocol_value !== typeof undefined && quality_protocol_value !== false) {
                    ret = quality_protocol_value;
                }
                else{
                    ret = elem.value;
                }

                return typeof ret === "string" ?
                    // handle most common string cases
                    ret.replace(rreturn, "") :
                    // handle cases where value is null/undef or number
                    ret == null ? "" : ret;
            }
            return;
        }
        else{
            return jqVal.call(this, value);
        }
    }
