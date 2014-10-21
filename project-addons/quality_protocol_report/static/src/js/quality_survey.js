$(document).ready(function() {
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
        console.log(date);
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

$(function () {
    $('#all_data').find('.quality_form').each(function() {
        var record = Number($(this).attr("record"));
        var model = $(this).attr("model");
        var context = {lang: 'es_ES', tz: 'Europe/Madrid'};
        $(this).find('.quality_field').each(function() {
            var field_to_represent = $(this).attr("qfield");
            var columns = $(this).attr("columns").split(",");
            var columns_options = $(this).attr("columns-options") ? eval('(' + $(this).attr("columns-options") + ')') : {};
            var columns_widths = $(this).attr("columns-widths") ? $(this).attr("columns-widths").split(',') : [];
            var no_delete_option = $(this).attr("nodelete") ? $(this).attr("nodelete") : false;
            var no_insert_option = $(this).attr("noinsert")  ? $(this).attr("noinsert") : false;
            var self = $(this);
            var obj = new openerp.web.Model(model, context);
            obj.call("fields_get", [field_to_represent], {context: context}).then(function(field_data) {
                console.log(field_data[field_to_represent]);
                var view_model = new openerp.web.Model(field_data[field_to_represent].relation, context);
                var table_columns = [];
                var format_columns = {};
                view_model.call("fields_get", [columns], {context: context}).then(function(fields) {
                    for (var i = 0; i<columns.length; i++) {
                        var key = columns[i];
                        if (key === "id") {
                            table_columns.push({name: key, type: 'hidden'});
                        }
                        else {
                            var ctrlProp = {};
                            var displayCss = {};
                            var uiOption = {};
                            if (fields[key].required) {
                                ctrlProp['required'] = true;
                            }
                            if (columns_options && columns_options[key] == "disabled") {
                                ctrlProp['disabled'] = true;
                            }
                            if (columns_widths.length > 0) {
                                displayCss['width'] = columns_widths[i];
                            }
                            format_columns[key] = fields[key].type;

                            if (JQUERY_UI_TYPES[fields[key].type] == "ui-datepicker") {
                                uiOption['dateFormat'] = 'dd/mm/yy'
                            }

                            table_columns.push({name: key, display: fields[key].string, type: JQUERY_UI_TYPES[fields[key].type], ctrlProp: ctrlProp, displayCss: displayCss, uiOption: uiOption});

                        }
                    }
                obj.call('read', [record, [field_to_represent]], {context: context}).then(function(response) {
                    if (response[field_to_represent].length > 0) {
                        var initData = [];
                        view_model.call('read', [response[field_to_represent], columns], {context: context}).then(function(rows_data) {
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
                                    initRows: 5,
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
                                    customRowButtons: no_delete_option ? [] : [
                                                        { uiButton: { icons: { primary: 'ui-icon-delete' }, text: false }, click: deleteRow, btnCss: { 'min-width': '20px' }, btnAttr: { title: 'Remove row' }, atTheFront: true },
                                                    ]
                                });
                        })
                    }
                    else {
                        self.appendGrid({
                            initRows: 5,
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
                            customRowButtons: no_delete_option ? [] : [
                                                { uiButton: { icons: { primary: 'ui-icon-delete' }, text: false }, click: deleteRow, btnCss: { 'min-width': '20px' }, btnAttr: { title: 'Remove row' }, atTheFront: true },
                                            ]
                        });
                    }

                });
                });
            });


        });
    });
});

//Falta pepararlo para multiples tablas
function deleteRow(evtObj, uniqueIndex, rowData) {
    console.log(rowData);
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

/*se envia los datos de las diferentes encuestas al servidor(funcion en controller de survey).
  Se hace una llamada por encuesta y página.
  Luego se llama a una función del modulo para que relacione el numero de serie con las respuestas.
*/
function send_form_server() {
    if ($("#exist").length === 0) {
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
                        console.log("entra aqui")
                    },
                    success: function(response, status, xhr, wfe) { // submission attempt
                        console.log("entra en success")
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
                        console.log("entra en fallo ajax")
                        $('#AJAXErrorModal').modal('show');
                        $("#all_data :input").attr("disabled", false);
                        $("#send_form").show();
                    }
                });
            });

        });
    };
    $('#all_data').find('.view').each(function() {
        var context = {lang: 'es_ES', tz: 'Europe/Madrid'};
        if ($(this).find("form").length) {
            var base_model = $(this).find("form").attr("model");
            var base_record = Number($(this).find("form").attr("record"));
            var obj = new openerp.web.Model(base_model, context);
            var dat = decodeURIComponent($(this).find("form").serialize());
            console.log(dat);
            $(this).find("form").find(".quality_field").each(function() {
                var form_field = $(this).attr("qfield");
                var table_id = $(this).attr("id");
                var records = {};
                var elements = dat.split('&');
                for (var i = 0; i< elements.length; i++) {
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
                    if (row_index in records) {
                        records[row_index][field_name] = vals[1];
                    }
                    else {
                        records[row_index] = {};
                        records[row_index][field_name] = vals[1];
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
                        fields[form_field] = [[2, to_remove_rows[i]]];
                        obj.call("write", [base_record, fields], {context: context});
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
                        console.log("update");
                        var update_id = records[row].id;
                        delete records[row].id;
                        fields[form_field] = [[1, Number(update_id), records[row]]];
                        obj.call("write", [base_record, fields], {context: context});
                    }
                    else {
                        console.log("insert");
                        delete records[row].id;
                        fields[form_field] = [[0, 0, records[row]]];
                        obj.call("write", [base_record, fields], {context: context});
                    }
                }
        });
        $(this).find("form").find(".form-control").each(function() {
            var input_value = $(this).attr("value");
            var name = $(this).attr("name");;
            console.log(input_value);
            console.log(name);
            var fields = {};
            fields[name] = input_value;
            obj.call("write", [base_record, fields], {context: context});
        });
    }
    });

}
