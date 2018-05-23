var observador = new MutationObserver(function(cambios) {
    cambios.forEach(function(cambio) {
        var nuevosNodos = cambio.addedNodes;
        if (nuevosNodos !== null) {
            var $nodos = $(nuevosNodos);
            $nodos.each(function() {
                var $nodo = $(this);
                if ($nodo.is('tbody') && $nodo.find('td[data-field="analysis_type"]')) {
                    $nodo.closest('table').addClass('objetivo').attr('id', 'objetivo');
                };
            });
            aplicarRestricciones();
        }
    });
});

function desactivarCampos(obj, campos) {
    $.each(campos, function(idx, val) {
        $(obj).find('td[data-field="' + val + '"]').not('.desactivado').addClass('desactivado').click(false);
    });
};

function desactivarEnFormulario(obj) {
    $(obj).find('td[data-field]').each(function() {
        var campo = $('span[data-fieldname="' + $(this).data('field') + '"]');
        if (campo) {
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

function aplicarRestricciones() {
    $('table.objetivo tr').each(function(idx) {
        var tr = this;

        desactivarCampos(tr, [
            'proposed', 'analysis_type', 'expected_result', 'passed',
            'decimal_precision', 'expr_error', 'raw_material_analysis',
            'expected_result_expr', 'expected_result_boolean', 'result'
        ]);

        if ($(tr).find('td[data-field="raw_material_analysis"] input:checked').length == 1) {
            desactivarCampos(tr, ['method', 'result_boolean_selection', 'result_str', 'realized_by']);
        };

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
                desactivarEnFormulario(this);
                $(this).dequeue();
            });
        });
    });
};

$(function() {
    $('head').append('<link rel="stylesheet" type="text/css" href="product_analysis/static/src/css/analysis_table.css"/>');

    ap = $('td.oe_application');
    if (ap.length !== 0) {
        observador.observe(ap[0], {childList: true, subtree: true});
    };
});