class sensor {
    constructor() {
        this.ultimaCaptura = 0;  // Unix timestamp de la última captura obtenida
        this.ipServidor = '10.10.21.15';  // IP del servidor que nos proporciona los datos
        this.sensor = '';  // Identificador del sensor del que se pedirán los datos
        this.temporizador = false;  // Handle del temporizador que irá consultando si hay datos nuevos
        this.funcionTemporizador = function() { return false; };  // Función desde la que llamaremos a dameDatos() periódicamente
        this.capturaDetenida = true;  // Con esto indicamos si el proceso de captura de datos está en marcha o no
        this.tiempoEntreLecturas = 2000;  // Lapso de espera en segundos entre peticiones de consulta de los datos
        this.recogeDatos = function(datos) {  // Método que deberíamos sobreescribir para trabajar con los datos recibidos
            alert(JSON.stringify(datos));
            return false;
        };
        this.dameDatos = function() {  // Método que solicitará al servidor el último dato disponible
            var obj = this;
            // Detenemos el temporizador mientras esperamos por una respuesta
            // Esto se hace para evitar posibles solapamientos entre peticiones
            obj.pausarCaptura();
            // Pedimos datos al servidor
            $.get('http://' + obj.ipServidor + '/dame_datos.php', {sensor: obj.sensor}, function(datos) {
                d = JSON.parse(datos);
                // Si no hay datos nuevos, no hacemos nada. En caso contrario, recogemos los datos...
                if (d.length > 0 && parseInt(d[0].captura.$date.$numberLong) > obj.ultimaCaptura) {
                    // Si es la primera captura, la usamos únicamente como
                    // punto de partida para empezar a leer a partir de ahí
                    if (obj.ultimaCaptura > 0) {
                        obj.recogeDatos(d[0]);
                    }
                    obj.ultimaCaptura = parseInt(d[0].captura.$date.$numberLong);
                }
                // Si no se ha detenido explícitamente el temporizador, lo reactivamos
                if (obj.temporizador == false && !obj.capturaDetenida) {
                    obj.iniciarCaptura();
                }
            });
        };
        this.iniciarCaptura = function() {
            this.temporizador = setInterval(this.funcionTemporizador, this.tiempoEntreLecturas);
            this.capturaDetenida = false;
        };
        this.pausarCaptura = function() {
            clearInterval(this.temporizador);
            this.temporizador = false;
        };
        this.detenerCaptura = function() {
            // Detenemos el temporizador de captura
            if (this.temporizador != false) {
                clearInterval(this.temporizador);
                this.temporizador = false;
            };
            this.capturaDetenida = true;
        };
        this.tabla = {  // Si trabajamos con una tabla, aquí englobamos todos sus parámetros
            padre: false,  // Hace referencia a la instancia del sensor al que pertenece esta tabla
            $tabla: false,  // Objeto jQuery de la tabla donde capturaremos datos, si procede
            campos: false,  // Cadena de texto o array con los campos de la tabla a rellenar
            $campoVigilado: false,  // Campo donde insertaremos el dato que recibamos
            $campoSiguiente: false,  // Campo donde llevaremos el foco una vez recibido el dato en el vigilado
            capturaPropiedad: function(propiedad) {  // Con este método, iremos volcando una única propiedad en los
                var obj = this;                      // distintos campos especificados de la fila activa de la tabla
                var idTabla = obj.$tabla.attr('id');
                obj.padre.funcionTemporizador = function() {
                    var e = document.activeElement;
                    var $e = $(e);
                    // Comprobamos si estamos en un campo de la tabla objetivo
                    if (e.nodeName == 'INPUT' && $e.parents('table').attr('id') == idTabla) {
                        var id = $e.attr('id');
                        if (id !== undefined) {
                            for (var idx = 0; idx < obj.campos.length; idx++) {
                                // Si el campo activo pertenece a la tabla y este no tiene ya datos
                                if (id.includes(idTabla + '_' + obj.campos[idx] + '_') && $e.val() == '') {
                                    obj.campoVigilado = $e;
                                    // Buscamos el siguiente campo que recibirá el próximo dato
                                    obj.campoSiguiente = $e;
                                    if (idx < obj.campos.length - 1) {
                                        obj.campoSiguiente = $('input#' + id.replace(obj.campos[idx], obj.campos[idx + 1]));
                                    }
                                    // Preguntamos al servidor si hay datos nuevos
                                    obj.padre.dameDatos();
                                    break;
                                }
                            }
                        }
                    } else {
                        // No estamos sobre un campo de la tabla objetivo
                        obj.campoVigilado = false;
                        obj.campoSiguiente = false;
                    }
                };

                // Siempre que empecemos la captura, limpiamos objetivos
                obj.campoVigilado = false;
                obj.campoSiguiente = false;

                // Si la propiedad campos es una cadena de texto, la convertimos a array
                if (typeof obj.campos === 'string' && obj.campos.includes(',')) {
                    obj.campos = obj.campos.split(',');
                }

                // Definimos cómo queremos procesar los datos recibidos
                obj.padre.recogeDatos = function(datos) {
                    // Si tenemos campo con el foco para recibir el dato, lo cubrimos
                    if (obj.campoVigilado instanceof jQuery) {
                        obj.campoVigilado.val(datos[propiedad]);
                    }
                    // Saltamos al siguiente campo que recibirá el próximo dato
                    if (obj.campoSiguiente instanceof jQuery) {
                        obj.campoSiguiente.focus();
                    }
                };

                // Comenzamos a vigilar si hay datos nuevos para la tabla objetivo
                obj.padre.iniciarCaptura();
            },
        };

        // Indicamos a la tabla quién es su padre, al más puro estilo de Darth Vader
        this.tabla.padre = this;
    }
};