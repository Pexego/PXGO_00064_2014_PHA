$(document).ready(function () {
    'use strict';
    $("#send_form").click(send_form_server);
});

/*se envia los datos de las diferentes encuestas al servidor(funcion en controller de survey).
  Se hace una llamada por encuesta y página.
  Luego se llama a una función del modulo para que relacione el numero de serie con las respuestas.
*/
function send_form_server(){
    $(".datos_survey").each(function(){
        $('.js_errzone').html("").hide();
        var url_submit = $(this).attr("url_submit");

        $(this).find(".survey_page").each(function(){
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
                            _.each(_.keys(response.errors), function(key){
                                $("#" + key + '>.js_errzone').append('<p>' + response.errors[key] + '</p>').show();
                            });
                            console.log("entra en error")
                            return false;
                        }
                        else if (_.has(response, 'redirect')){      // form is ok
                            $("#general_info").html("");
                            $("#general_info").append('<p>Respuestas enviadas.</p>').show();
                        }
                        else {                                      // server sends bad data
                            console.error("Incorrect answer sent by server");
                            return false;
                        }
                    },
                    timeout: 5000,
                    error: function(jqXHR, textStatus, errorThrown){ // failure of AJAX request
                        console.log("entra en fallo ajax")
                        $('#AJAXErrorModal').modal('show');
                    }
                });
            });
        });

    });

}

