$(document).ready(function () {
    'use strict';
    console.log("inicio js");
    $("#send_form").click(function() {
  console.log( "Handler for .click() called." );
});
});

/*se envia los datos de las diferentes encuestas al servidor(funcion en controller de survey).
  Se hace una llamada por encuesta y página.
  Luego se llama a una función del modulo para que relacione el numero de serie con las respuestas.
*/
function send_form_server(){
    // url para submit: /survey/submit/<model("survey.survey"):survey>'
    /*
     * TODO: recorrer los div class="survey" la url para submit se encuentra en la propiedad url_submit del div de cada encuesta
     * en cada página enviar las respuestas al servidor
     * por post:
     *      page_id: pagina de la encuesta
     *      token: token de la respuesta
     *      para cada pregunta de la página:
     *          la respuesta con clave surveyid_pageid_questionid
     *
     */

}
