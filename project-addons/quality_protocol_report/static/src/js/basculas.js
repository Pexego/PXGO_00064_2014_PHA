function bascula() {
    this.ultimaPesada = 0;
    this.ipServidor = '10.10.21.15';
    this.bascula = '';
    this.temporizador = false;
    this.tiempoEntreLecturas = 2000;  // Lapso de espera en segundos entre peticiones de lectura de las pesadas
    this.damePesada = function(campo, campoSiguiente) {  // "campo" y "campoSiguiente" son objetos jQuery de tipo input
        obj = this;
        $.get('http://' + obj.ipServidor + '/dame_pesada.php', {bascula: obj.bascula}, function(datos) {
            d = JSON.parse(datos);
            if (d.length > 0 && parseInt(d[0].captura.$date.$numberLong) > obj.ultimaPesada) {
                obj.ultimaPesada = parseInt(d[0].captura.$date.$numberLong);
                // Si tenemos campo con el foco para recibir pesada, lo cubrimos
                if (campo instanceof jQuery) {
                    campo.val(d[0].peso);
                }
                // Saltamos al siguiente campo que recibirá la próxima pesada
                if (campoSiguiente instanceof jQuery) {
                    campoSiguiente.focus();
                }
            }
        });
    };
    this.vigilaTabla = function(idTabla, listaCampos) {
        var campos = listaCampos.split(',');
        this.temporizador = setInterval(
            function() {
                var e = document.activeElement;
                var $e = $(e);
                if (e.nodeName == 'INPUT' && $e.parents('table').attr('id') == idTabla) {
                    var id = $e.attr('id');
                    if (id !== undefined) {
                        for (var idx = 0; idx < campos.length; idx++) {
                            if (id.includes(idTabla + '_' +  campos[idx]) && $e.val() == '') {
                                var $siguiente = $e;
                                if (idx < campos.length - 1) {
                                    $siguiente = $('input#' + id.replace(campos[idx], campos[idx + 1]));
                                }
                                miBascula.damePesada($e, $siguiente);
                                break;
                            }
                        }
                    }
                }
            }, this.tiempoEntreLecturas
        );
    }
};
