var all_ok = true;
$(document).ready(function () {
    'use strict';
    $("#send_form").click(send_form_server);
    /*$.ajaxComplete(function() {
        if(all_ok == true){
            $("#all_data :input").attr("disabled", true);
            $("#send_form").hide();
            $("#general_info").append('<p>Respuestas enviadas.</p>').show();
        }
    });*/
});

/*se envia los datos de las diferentes encuestas al servidor(funcion en controller de survey).
  Se hace una llamada por encuesta y página.
  Luego se llama a una función del modulo para que relacione el numero de serie con las respuestas.
*/
function send_form_server(){
    $('.js_errzone').html("").hide();
    $('#all_data').find('.survey').each(function(){
        var url_submit = $(this).attr("url_submit");

        $(this).find("form").each(function(){
            $.ajax({
                url: url_submit,
                type: 'POST',                       // submission type
                data: $(this).serialize(),
                dataType: 'json',                   // answer expected type
                beforeSubmit: function(){           // hide previous errmsg before resubmitting
                    $('.js_errzone').html("").hide();
                    console.log("entra aqui")
                },
                success: function(response, status, xhr, wfe){ // submission attempt
                    console.log("entra en success")
                    if(_.has(response, 'errors')){  // some questions have errors
                        all_ok = false;
                        _.each(_.keys(response.errors), function(key){
                            $("#" + key + '>.js_errzone').append('<p>' + response.errors[key] + '</p>').show();
                        });
                    }
                    else if(_.has(response, 'redirect')){
                        console.log("todo bien")
                    }
                    else {                                      // server sends bad data
                        console.error("Incorrect answer sent by server");
                        all_ok = false;
                    }
                },
                timeout: 5000,
                error: function(jqXHR, textStatus, errorThrown){ // failure of AJAX request
                    console.log("entra en fallo ajax")
                    $('#AJAXErrorModal').modal('show');
                    all_ok = false;
                }
            });
        });

    });

}

