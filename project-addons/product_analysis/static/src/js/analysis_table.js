function desactivarCampos(obj, campos) {
    $.each(campos, function(idx, val) {
        $(obj).find('td[data-field="' + val + '"]')
              .not('.desactivado')
              .addClass('desactivado')
              .unbind('click')
              .bind('click', false);
    });
};

function desactivarEnFormulario(obj) {
    $(obj).find('td[data-field]').each(function() {
        var campo = $('span[data-fieldname="' + $(this).data('field') + '"]');
        if (campo.length) {
            if ($(this).hasClass('desactivado')) {
                $(campo).find('input').prop('disabled', true);
                $(campo).find('select').prop('disabled', true);
                $(campo).find('span.oe_m2o_drop_down_button').hide();
            } else {
                $(campo).find('input').prop('disabled', false);
                $(campo).find('select').prop('disabled', false);
                $(campo).find('span.oe_m2o_drop_down_button').show();
            };
        };
    });
};

function aplicarRestricciones(tabla) {
    $(tabla).find('tr').not('[data-id="false"]').each(function(idx) {
        var tr = this;

        desactivarCampos(tr, [
            'proposed', 'method', 'analysis_type', 'expected_result',
            'decimal_precision', 'raw_material_analysis',
            'expected_result_expr', 'expected_result_boolean', 'criterion'
        ]);

//        if ($(tr).find('td[data-field="raw_material_analysis"] input:checked').length == 1) {
//            desactivarCampos(tr, ['result_boolean_selection', 'result_str', 'realized_by']);
//        };

        if ($(tr).find('td[data-field="proposed"] input:checked').length == 1) {
            desactivarCampos(tr, ['analysis_id']);
        };

        $(tr).find('td[data-field="analysis_type"]').each(function() {
            if ($(this).text() == 'Booleano') {
                desactivarCampos(tr, ['result_str']);
            } else {
                desactivarCampos(tr, ['result_boolean_selection']);
            };
        });

        $(tr).unbind('click.objetivo').bind('click.objetivo', function(e) {
            $(this).delay(500).queue(function() {
                comprobarFormulario();
                desactivarEnFormulario(this);
                $(this).dequeue();
            });
        });
    });
};

function comprobarFormulario() {
    var wizard = $('div#stockLotAnalysisWizard');
    if (wizard.length) {
        wizard = wizard[0]
        if (!('tabla' in wizard)) {
            wizard.tabla = $(wizard).find('td[data-field="analysis_type"]')
                                    .closest('table')
            $(wizard.tabla).addClass('objetivo').attr('id', 'objetivo');
            aplicarRestricciones(wizard.tabla);
        };

        var campo = $(wizard).find('span.oe_form_field[data-fieldname="analysis_id"]');
        if (campo.length) {
            campo = campo[0]
            var posicion = $(campo).css('top');
            if (!('posicion' in campo) || (campo.posicion !== posicion)) {
                campo.posicion = posicion;
                aplicarRestricciones(wizard.tabla);
            };
        };
    };
};

$(function() {
    var d = new Date();
    $('head').append('<link rel="stylesheet" type="text/css" ' +
                     'href="product_analysis/static/src/css/analysis_table.css' +
                     '?t=' + d.getTime().toString() + '"/>');

    var dialogo = $('.modal-dialog');
    if (dialogo) {
        dialogo.attr('id', 'stockLotAnalysisWizard');  // Ponemos la diana
        setTimeout(comprobarFormulario, 1000);
    };
});