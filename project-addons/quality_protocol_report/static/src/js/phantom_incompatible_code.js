function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function botonRellenarClick(e) {
    var data = $(this).data(),
        parent = $(this).parent(),
        template = '',
        campoFoco = $(this).attr('foco');

    if (parent[0].nodeName == 'TD') {  // Si el botón está en una celda de una tabla
        parent = parent.parent();  // Subimos al tr padre
        template = parent.attr('id');
    } else {
        parent = $(this.form);  // Si no estamos en una tabla, buscamos el formulario
    }

    parent.find('input, textarea').each(async function(idx, field) {
        var fieldName = field.name;
        if (template > '') {
            var pos = template.indexOf('_Row_'),
                beginWord = template.substring(0, pos + 1),
                endWord = template.substring(pos + 4);
            fieldName = fieldName.match(new RegExp(beginWord + "(.*)" + endWord))[1];
        }
        if (fieldName in data) {
            var txt = data[fieldName];

            if (typeof txt === 'string') {
                if (txt.includes('[hora]')) {
                    dameFechaHoraServidor('hora');
                    do {await sleep(200);} while (!horaServidor);
                    txt = txt.replace('[hora]', horaServidor);
                }
                if (txt.includes('[fecha]')) {
                    dameFechaHoraServidor('fecha');
                    do {await sleep(200);} while (!fechaServidor);
                    txt = txt.replace('[fecha]', fechaServidor);
                }
                if (txt.includes('[fecha_hora]')) {
                    dameFechaHoraServidor('fecha_hora');
                    do {await sleep(200);} while (!fechaHoraServidor);
                    txt = txt.replace('[fecha_hora]', fechaHoraServidor);
                }
            }
            field.value = txt;
        }
    });

    if (campoFoco !== undefined) {
        if (template > '') {
            var pos = template.indexOf('_Row_'),
                beginWord = template.substring(0, pos + 1),
                endWord = template.substring(pos + 4);
            campoFoco = beginWord + campoFoco + endWord;
        }
        parent.find('[name="' + campoFoco + '"]').focus();
    }
}
