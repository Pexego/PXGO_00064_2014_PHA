$(document).ready(function () {
    'use strict';
    $("#send_form").click(send_form_server);
    // Si el div #exist existe se rellenan las preguntas por ajax.
    if($("#exist").length != 0) {
        $("#all_data :input").attr("disabled", true);
        $("#send_form").hide();
        fill_data();
    }
});


function fill_data(){
     $('#all_data').find('.survey').each(function(){
        var url_fill = $(this).attr("fill");

        $(this).find("form").each(function(){
            var the_form = $(this);
            $.ajax(url_fill, {dataType: "json"})
                .done(function(json_data){
                    _.each(json_data, function(value, key){
                        the_form.find(".form-control[name=" + key + "]").val(value);
                        the_form.find("input[name^=" + key + "]").each(function(){
                            $(this).val(value);
                        });
                    });
                })
                .fail(function(){
                    console.warn("[survey] Unable to load prefill data");
                });
        });
    });
}

/*se envia los datos de las diferentes encuestas al servidor(funcion en controller de survey).
  Se hace una llamada por encuesta y página.
  Luego se llama a una función del modulo para que relacione el numero de serie con las respuestas.
*/
function send_form_server(){
    $('.js_errzone').html("").hide();
    $('#all_data').find('.survey').each(function(){
        var url_submit = $(this).attr("url_submit");
        var dat = $(this).find("form").serialize();
        // Si se cambia a disabled antes de serializar falla
        $(this).find(":input").attr("disabled", true);
        $(this).find("form").each(function(){
            $.ajax({
                url: url_submit,
                type: 'POST',                       // submission type
                data: dat,
                dataType: 'json',                   // answer expected type
                beforeSubmit: function(){           // hide previous errmsg before resubmitting
                    $('.js_errzone').html("").hide();
                    console.log("entra aqui")
                },
                success: function(response, status, xhr, wfe){ // submission attempt
                    console.log("entra en success")
                    if(_.has(response, 'errors')){  // some questions have errors
                        $("#all_data :input").attr("disabled", false);
                        _.each(_.keys(response.errors), function(key){
                            $("#" + key + '>.js_errzone').append('<p>' + response.errors[key] + '</p>').show();
                        });
                    }
                    else if(_.has(response, 'redirect')){
                        //No se tienen en cuenta los mensajes de redireccion.
                    }
                    else {                                      // server sends bad data
                        console.error("Incorrect answer sent by server");
                        $("#all_data :input").attr("disabled", false);
                    }
                },
                timeout: 5000,
                error: function(jqXHR, textStatus, errorThrown){ // failure of AJAX request
                    console.log("entra en fallo ajax")
                    $('#AJAXErrorModal').modal('show');
                    $("#all_data :input").attr("disabled", false);
                }
            });
        });

    });

}

