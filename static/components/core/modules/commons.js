/**
 * Modulo de JS Comun
 */
var tipo_comprobante_seleccionado = null;
var id_comprobante_seleccionado = null;

var TITULO_ANULACION_COMPROBANTE = '<span style="color:#EE0000">ATENCIÓN!</span>';
var MENSAJE_ANULACION_COMPROBANTE = 'Este es un proceso informativo y debe ejecutarse una vez que ha anulado los comprobante en el portal del SRI (opción Solicitud Anulación Comprobantes).<br><br>Cambiará el estado del comprobante.¿Desea Continuar?';
var MENSAJE_ACTIVACION_COMPROBANTE = 'Se procederá a Re-Activar el comprobante anulado. Esto hará que sus clientes también lo puedan visualizar entre sus comprobantes recibidos.<br><br>¿Desea Continuar?';
var MENSAJE_ERROR_INGRESO_CODIGO = '<b style="color:#EE0000">ATENCIÓN!</b><br>El codigo de anulación del SRI debe tener 9 dígitos.';
var MENSAJE_ERROR_INGRESO_CODIGO_FACT = '<b style="color:#EE0000">ATENCIÓN!</b><br>La clave de acceso debe ser de 49 digitos y el numero de autorizacion de 37 digitos.';

function renderSelectOptions(component_id, items) {
   $('#'+component_id).html('');
   $('#'+component_id).append('<option selected="selected" value="">----</option>');
   $.each(items, function(i, item) {
      $('#'+component_id).append('<option value="'+item.id+'">'+item.value+'</option>');
   });
   hideWait();
};

function showWait() {
   $('#pleaseWaitDialog-alert').html('');
   try {
      $('#pleaseWaitDialog').modal('show');
   }catch(e) {
       $('#openWaitDialog').click();
   }
};

function hideWait() {
   try {
      $('#pleaseWaitDialog').modal('hide');
   }catch(e) {
       $('#closeWaitDialog').click();
   }
   $('#pleaseWaitDialog-alert').html('');
};

function showSmallWait() {
   $('#small_wait_spinner').removeClass('hidden');
};

function hideSmallWait() {
   $('#small_wait_spinner').addClass('hidden');
};

function agregar_bandeja_impresion(entity_id, entity_type) {
   Dajaxice.emisor_receptor.agregar_bandeja_impresion(Dajax.process, {'entity_id':entity_id, 'entity_type':entity_type});
};

function mostrarModalImpresion(cuenta) {
   if (cuenta) {
      $('#printer_modal_question').html("<p>Tiene "+cuenta+" elemento(s) en la Bandeja de Impresión de Innobee. Desea imprimirlo(s) ahora?</p>");
   }
   $('#printer_modal').modal('show');
};

function mostrarWarningModalImpresion() {
   $('#printer_modal_warning').modal('show');
};

function banner_click(banner_id) {
   Dajaxice.emisor_receptor.banner_click(Dajax.process, {'banner_id':banner_id});
};

function seleccionar_comprobante_accion(tipo_comp, id_comp) {
   tipo_comprobante_seleccionado = tipo_comp;
   id_comprobante_seleccionado = id_comp;
   $('#accion_comprobante_modal').modal('show');
};

function activar_autorizacion_comprobante(tipo_comp, id_comp) {
   var $elem = $('#'+tipo_comp+"-"+id_comp+" .conf-comp");
   $elem.html('<i class="glyphicon glyphicon-ok" rel="tooltip" title="AUTORIZADO"></i>&nbsp;');
   $elem.attr("href","#");
   $elem.attr("rel","");
   $elem.attr("title","");
   $elem.attr("class","conf-comp btn btn-primary");   
   $('#accion_comprobante_modal').modal('hide');
};

function activar_rechazo_comprobante(tipo_comp, id_comp) {
   var $elem = $('#'+tipo_comp+"-"+id_comp+" .conf-comp");
   $elem.html('<i class="glyphicon glyphicon-remove" rel="tooltip" title="RECHAZADO"></i>&nbsp;');
   $elem.attr("href","#");
   $elem.attr("rel","");
   $elem.attr("title","");
   $elem.attr("class","conf-comp btn btn-primary");   
   $('#accion_comprobante_modal').modal('hide');
};

var intervalShowHide = null;
function aceptar_comprobante_recibido() {
   var observaciones = $('#observaciones_comprobante_recibido').val();
   $('#rechazar_comprobante_button').hide(); 
   intervalShowHide = setInterval(function() { $('#rechazar_comprobante_button').show(); clearInterval(intervalShowHide); }, 1000);
   Dajaxice.emisor_receptor.aceptar_comprobante_recibido(Dajax.process,
      {'tipo_comprobante':tipo_comprobante_seleccionado, 'comprobante_id':id_comprobante_seleccionado, 'observaciones':observaciones});
};

function rechazar_comprobante_recibido() {
   var observaciones = $('#observaciones_comprobante_recibido').val();
   var email_rechazo = $('#email_rechazo_comprobante_recibido').val();
   $('#rechazar_comprobante_button').hide(); 
   intervalShowHide = setInterval(function() { $('#rechazar_comprobante_button').show(); clearInterval(intervalShowHide); }, 6500);
   Dajaxice.emisor_receptor.rechazar_comprobante_recibido(Dajax.process,
      {'tipo_comprobante':tipo_comprobante_seleccionado, 'comprobante_id':id_comprobante_seleccionado,
      'observaciones':observaciones, 'email_rechazo':email_rechazo});
};

function filter_emitidos_form() {
   showWait();
   $('#filter_emitidos_button').prop('disabled', true);
   setTimeout(function() {$('#filter_emitidos_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_emitidos_form(Dajax.process,{'form':$('#filtro_emitidos_form').serialize()});
   return false;
};

function filter_recibidos_form() {
   showWait();
   $('#filter_recibidos_button').prop('disabled', true);
   setTimeout(function() {$('#filter_recibidos_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_recibidos_form(Dajax.process,{'form':$('#filtro_recibidos_form').serialize()});
   return false;
};

function filter_cargados_form() {
   showWait();
   $('#filter_cargados_button').prop('disabled', true);
   setTimeout(function() {$('#filter_cargados_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_cargados_form(Dajax.process,{'form':$('#filtro_cargados_form').serialize()});
   return false;
};

function filter_banners_form() {
   showWait();
   $('#filter_banners_button').prop('disabled', true);
   setTimeout(function() {$('#filter_banners_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_banners_form(Dajax.process,{'form':$('#filtro_banners_form').serialize()});
   return false;
};

function filter_cupones_form() {
   showWait();
   $('#filter_cupones_button').prop('disabled', true);
   setTimeout(function() {$('#filter_cupones_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_cupones_form(Dajax.process,{'form':$('#filtro_cupones_form').serialize()});
   return false;
};

function filter_productos_form() {
   showWait();
   $('#filter_productos_button').prop('disabled', true);
   setTimeout(function() {$('#filter_productos_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_productos_form(Dajax.process,{'form':$('#filtro_productos_form').serialize()});
   return false;
};

function filter_campanias_form() {
   showWait();
   $('#filter_campanias_button').prop('disabled', true);
   setTimeout(function() {$('#filter_campanias_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_campanias_form(Dajax.process,{'form':$('#filtro_campanias_form').serialize()});
   return false;
};

function filter_campanias_sms_form() {
   showWait();
   $('#filter_campanias_sms_button').prop('disabled', true);
   setTimeout(function() {$('#filter_campanias_sms_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_campanias_sms_form(Dajax.process,{'form':$('#filtro_campanias_sms_form').serialize()});
   return false;
};

function filter_campanias_email_form() {
   showWait();
   $('#filter_campanias_email_button').prop('disabled', true);
   setTimeout(function() {$('#filter_campanias_email_button').prop('disabled', false); return false;}, 2000);
   Dajaxice.emisor_receptor.filter_campanias_email_form(Dajax.process,{'form':$('#filtro_campanias_email_form').serialize()});
   return false;
};

function paginar(page, pagination_type) {
   showWait();
   Dajaxice.emisor_receptor.pagination(Dajax.process,{'p':page, 'p_type':pagination_type });
   return false;
};

function cambiar_estado_comprobante(tipo_comp, id_comp, estado) {
   var texto = estado == 1? MENSAJE_ANULACION_COMPROBANTE : MENSAJE_ACTIVACION_COMPROBANTE;
   bootbox.dialog({
      title: TITULO_ANULACION_COMPROBANTE,
      message:  '<div class="row"> ' +
      '<div class="col-md-12"> ' +
      '<p>'+texto+'</p>' +
      '<form class="form-horizontal"> ' +
      '<div class="form-group"> ' +
      '<label class="col-md-6 control-label" for="codigo_anulacion_sri">Código Anulación SRI</label> ' +
      '<div class="col-md-6"> ' +
      '<input id="codigo_anulacion_sri" name="codigo_anulacion_sri" type="text" placeholder="000000000" class="form-control input-md"> ' +
      '<span class="help-block">Ingrese el código entregado por el SRI al realizar la anulación</span> </div> ' +
      '</div>' +
      '</form> </div> </div>',
       buttons: {
         cancel: {
            label: "Cancelar",
            className: "btn",
         },
         success: {
            label: "Aceptar",
            className: "btn-success",
            callback: function () {
               var codigo = $('#codigo_anulacion_sri').val();
               if(codigo && codigo.length == 9) {
                  Dajaxice.emisor_receptor.cambiar_estado_comprobante(Dajax.process,
                  {'tipo_comprobante':tipo_comp, 'comprobante_id':id_comp, 'codigo_anulacion':codigo});
               }
               else {
                  bootbox.alert(MENSAJE_ERROR_INGRESO_CODIGO);
               }
               
            }
         }
      }
   });   
};

function cambiar_estado_factura(tipo_comp, id_comp, estado) {
   var texto = estado == 1? MENSAJE_ANULACION_COMPROBANTE : MENSAJE_ACTIVACION_COMPROBANTE;
   var formulario = '<form class="form-horizontal"> ' +
      '<div class="form-group"> ' +
      '<label class="col-md-4 control-label" for="clave_acceso_nc">Clave Acceso Nota Credito</label> ' +
      '<div class="col-md-6"> ' +
      '<input id="clave_acceso_nc" class="form-control" type="text" placeholder="0000000000000000000000000000000000000000000000000" name="clave_acceso_nc" style="width:300px">' +
      '<span class="help-block">Ingrese la clave de acceso de la <br>nota de credito con la que anula la factura</span>' +
      '</div>' +
      '<div class="form-group"> ' +
      '<label class="col-md-4 control-label" for="numero_autorizacion">Numero de Autorización Nota Credito</label>' +
      '<div class="col-md-6"> ' +
      '<input id="numero_autorizacion" name="numero_autorizacion" type="text" placeholder="0000000000000000000000000000000000000" class="form-control" style="width:300px"> ' +
      '<span class="help-block">Ingrese el numero de autorización de la <br>nota de credito con el que se anula la factura</span> ' +
      '</div>' +
      '</div>' +
      '</form>';
      
   if(estado!=1) formulario='';
   
   bootbox.dialog({
      title: TITULO_ANULACION_COMPROBANTE,
      message:  '<div class="row"> ' +
      '<div class="col-md-12"> ' +
      '<p>'+texto+'</p>' +
      formulario +
      '</div> </div>',
       buttons: {
         cancel: {
            label: "Cancelar",
            className: "btn",
         },
         success: {
            label: "Aceptar",
            className: "btn-success",
            callback: function () {
               if(estado != 1) {
                  Dajaxice.emisor_receptor.cambiar_estado_comprobante(Dajax.process,
                     {'tipo_comprobante':tipo_comp, 'comprobante_id':id_comp, 'codigo_anulacion':'0' });
               }
               else {
                  var clave_acceso_nc = $('#clave_acceso_nc').val();
                  var numero_autorizacion = $('#numero_autorizacion').val();
                  if(clave_acceso_nc && clave_acceso_nc.length == 49 && numero_autorizacion && numero_autorizacion.length == 37 ) {
                     Dajaxice.emisor_receptor.cambiar_estado_comprobante(Dajax.process,
                     {'tipo_comprobante':tipo_comp, 'comprobante_id':id_comp, 'codigo_anulacion':clave_acceso_nc+'-'+numero_autorizacion });
                  }
                  else {
                     bootbox.alert(MENSAJE_ERROR_INGRESO_CODIGO_FACT);
                  }
               }
            }
         }
      }
   });   
};

/*
   RENOTIFICAR EL COMPROBANTE
*/
function reenotificar(tipo_comp, id_comp) {
   bootbox.dialog({
      title: 'Re-Notificacion via Email',
      message:  '<div class="row"> ' +
      '<div class="col-md-12"> ' +
      '<p>Ingrese hasta dos emails separados por comas</p>' +
      '<form class="form-horizontal"> ' +
      '<div class="form-group"> ' +
      '<label class="col-md-6 control-label" for="emails_notificacion">Correos Electr&oacute;nicos:</label> ' +
      '<div class="col-md-6"> ' +
      '<input id="emails_notificacion" name="emails_notificacion" style="width:350px !important" type="text" placeholder="micliente@dominio.com" class="form-control input-md"> ' +
      '</div> ' +
      '</div>' +
      '</form> </div> </div>',
       buttons: {
         cancel: {
            label: "Cancelar",
            className: "btn"
         },
         success: {
            label: "Aceptar",
            className: "btn-success",
            callback: function () {
               var emails_notificacion = $('#emails_notificacion').val();
               if(emails_notificacion) {
                   var emails = emails_notificacion.split(",");
                   if(emails.length > 2) {
                       bootbox.alert('Ingrese maximo dos emails.');
                   }
                   else {
                       var is_valid = true;
                       for(i = 0; i<emails.length; i++) {
                           if(!validateEmail(emails[i])) {
                               bootbox.alert('El email '+emails[i]+' no es valido.');
                               is_valid = false;
                               break;
                           }
                       }

                       if(is_valid) {
                           showWait();
                           Dajaxice.emisor_receptor.reenotificar(Dajax.process,
                            {'tipo_comprobante':tipo_comp, 'comprobante_id':id_comp, 'emails_notificacion':emails_notificacion});
                       }
                   }
               }
               else {
                  bootbox.alert('Es necesario ingresar al menos un email para re-notificar.');
               }

            }
         }
      }
   });
};

function restaurar_renotificacion() {
    bootbox.alert('Se ha renotificado su comprobante electronico');
};

function validateEmail(email) {
    var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
    return re.test(email);
};