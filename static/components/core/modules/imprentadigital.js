var elemento, targetElementId, elementoExtra, targetElementIdExtra;
var prefix;
var mensaje_comprobante="El comprobante ya ha sido Procesado, desea procesarlo de nuevo? Pulse OK para Continuar o Cancel para Cancelar.";

var TITULO_ANULACION_COMPROBANTE_DIGITAL = '<span style="color:#EE0000">ATENCIÓN!</span>';
var MENSAJE_ANULACION_COMPROBANTE_DIGITAL="<b>ATENCIÓN!</b><br>Este es un proceso informativo y debe ejecutarse una vez que ha anulado los comprobante en el portal del SRI (opción Solicitud Anulación Comprobantes). Cambiará el estado del comprobante.<br>¿Desea Continuar?";
var MENSAJE_ANULACION_COMPROBANTE_DIGITAL = 'Este es un proceso informativo y debe ejecutarse una vez que ha anulado los comprobante en el portal del SRI (opción Solicitud Anulación Comprobantes).<br><br>Cambiará el estado del comprobante.¿Desea Continuar?';
var MENSAJE_ERROR_INGRESO_CODIGO = '<b style="color:#EE0000">ATENCIÓN!</b><br>El codigo de anulación del SRI debe tener 9 dígitos.';
var MENSAJE_ERROR_INGRESO_CODIGO_FACT = '<b style="color:#EE0000">ATENCIÓN!</b><br>La clave de acceso debe ser de 49 digitos y el numero de autorizacion de 37 digitos.';

function search_result(data) {
    if(data && data.length > 0) {
        $(elemento).autocomplete({
            source: data,
            select: function( event, ui ) {
                if (ui.item && ui.item.value){
                    //console.log('Seleccionando '+ui.item.value);
                    var titleinput = ui.item.label;                
                    var id_elemento = elemento.name;
                    //console.log('Elemento '+id_elemento);
                    if(id_elemento.indexOf('id_') != 0) {
                        id_elemento = 'id_' + id_elemento;
                    }
                    id_elemento = id_elemento.replace('sf','id');
                    //console.log('Se ha seleccionado: '+ui.item.value+', estableciendo el valor en '+id_elemento);
                    $('#'+id_elemento).val(ui.item.value);
                    ui.item.value = titleinput;
                    return false;
                }
                
            }
        });
    }
};

function search_product(obj) {
    elemento = obj;
    Dajaxice.imprenta_digital.search_product(search_result,{'producto':$(obj).val()});
};

function filter_result(data) {
    if(data && data.length > 0) {
        $('#'+targetElementId).html('');
        $.each(data, function(i, item) {
           $('#'+targetElementId).append('<option value="'+item.value+'">'+item.label+'</option>');
        });
        hideSmallWait();
    }
};

function filter_result_extra(data) {
    if(data && data.length > 0) {
        $('#'+targetElementIdExtra).html('');
        $.each(data, function(i, item) {
            $('#'+targetElementIdExtra).append('<option value="'+item.value+'">'+item.label+'</option>');
            if(i == data.length-1) {
                //console.log('ANALIZE '+targetElementIdExtra);
                if(targetElementIdExtra.indexOf('porcentaje_retener') >= 0) {
                    //console.log('Actualizando >> '+targetElementIdExtra);
                    //update_field(targetElementIdExtra, 'porcentaje_retener', 'porcentaje_retener_tmp');
                }
            }
        });
        hideSmallWait();
    }
};
//a
function catalog_filter(obj, target, catalog_module, source_module, to_decimal) {
    console.log("source_module"+":"+source_module+"---"+"catalog_module"+":"+catalog_module+"target:"+target);
    showSmallWait();
    if(obj.id.indexOf('_set')>0) {
        targetElementId = get_set_field_id(obj, target);
    }
    else {
        targetElementId = target;
    }
    //console.log('NORMAL '+targetElementId);
    if(!source_module)
        Dajaxice.imprenta_digital.catalog_filter(filter_result,{'catalog_value':$(obj).val(), 'catalog_module':catalog_module, 'to_decimal':to_decimal});
    else
        Dajaxice.imprenta_digital.catalog_filter(filter_result,{'catalog_value':$(obj).val(), 'catalog_module':catalog_module,'source_module':source_module, 'to_decimal':to_decimal});
};

function catalog_filter_extra(obj, target, catalog_module, source_module) {
    showSmallWait();
    if(obj.id.indexOf('_set')>0) {
        targetElementIdExtra = get_set_field_id(obj, target);
    }
    else {
        targetElementIdExtra = target;
    }
    
    if(!source_module)
        Dajaxice.imprenta_digital.catalog_filter(filter_result_extra,{'catalog_value':$(obj).val(), 'catalog_module':catalog_module});
    else
        Dajaxice.imprenta_digital.catalog_filter(filter_result_extra,{'catalog_value':$(obj).val(), 'catalog_module':catalog_module,
                                                 'source_module':source_module});
        
    //console.log(target);
    if(target.indexOf('id_porcentaje_retener') >= 0) {
        var value = $(obj).val();
        if(value == '1') {
            show_field(obj, 'id_porcentaje_retener_tmp');
            hide_field(obj, 'id_porcentaje_retener');
            
           
        }
        else {
            show_field(obj, 'id_porcentaje_retener');
            hide_field(obj, 'id_porcentaje_retener_tmp');
        }
    }
    
};

function get_set_field_id(obj, target) {
    var parts = obj.id.split('-');
    var nombreModificado = '';
    for(i=0; i<parts.length-1; i++) {
        nombreModificado += parts[i] + '-';
    }
    nombreModificado += target.replace('id_', '');
    return nombreModificado;
};

function get_selectable_input_id(obj) {
    var input = $(obj).parent().children().first();
    var id_input = $(input).attr('id');
    if(!id_input) {
        input = $(input).next().next();
        id_input = $(input).attr('id');
    }
    console.log('id_input: '+id_input);
    return id_input;
}

function get_selectable_label_field(input_id) {
    return '#'+input_id.replace('_1','_0');
};

function get_selectable_value_field(input_id) {
    return '#'+input_id.replace('_0','_1');
};

function clear_product(obj) {
    var input_id = get_selectable_input_id(obj);
    $(get_selectable_label_field(input_id)).val('');
    $(get_selectable_value_field(input_id)).val('');
    recalc('#' + input_id.replace('id_producto_1','').replace('id_producto_0',''));
};

function new_product(obj) {
    var id_input = get_selectable_input_id(obj);
    var product_id = $(get_selectable_value_field(id_input)).val();
    var nombre_registro = id_input.replace('_1','_0');
    var initial_description = $(get_selectable_label_field(id_input)).val();
    showSmallWait();    
    Dajaxice.imprenta_digital.bind_product_form(Dajax.process,
        {'product_id':product_id,'nombre_registro':nombre_registro, 'initial_description':initial_description});
    return false;
};

function save_product() {
    var product_id = $('#id_id_registro').val();
    var firstFieldTaxes = $('#id_impdproductoimpuesto_set-0-codigo_impuesto').val();
    //console.log('firstFieldTaxes: '+firstFieldTaxes);
    if(firstFieldTaxes) {
        showWait();
        Dajaxice.imprenta_digital.save_product(Dajax.process,
                                    {'form':$('#form_crear_producto').serialize(true),
                                     'product_id':product_id});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert("Se requiere al menos de un impuesto para el producto.");
    }
    return false;
};

function search_customer(obj) {
    elemento = obj;
    Dajaxice.imprenta_digital.search_customer(search_result,{'cliente':$(obj).val()});
};

function consumidor_final(){
    alert("asd");
};

function search_customer_inline() {
    
    Dajaxice.imprenta_digital.search_customer_inline(Dajax.process,
                                {'tipo_identificacion':$('#id_tipo_identificacion').val(),
                                'identificacion':$('#id_identificacion').val(),
                                'ruc_empresa':$('#ruc_empresa').val()});
    return false;
};

function search_customer_inlineGR() {
    showSmallWait();
    //alert($('#id_ruc_empresa').val());
    Dajaxice.imprenta_digital.search_customer_inline_GR(Dajax.process,
                                {'tipo_identif_transportista':$('#id_tipo_identif_transportista').val(),
                                'ruc_empresa':$('#id_ruc_empresa').val(),'ruc_transportista':$('#id_ruc_transportista').val()});
    return false;
};

function save_customer() {
    Dajaxice.imprenta_digital.save_customer(Dajax.process,
                                {'form':$('#form_crear_cliente').serialize(true)});
    return false;
};

function save_factura() {
    var producto_id = $('#id_impditemfactura_set-0-id_producto_1').val();
    if(producto_id) {
        showWait();
        Dajaxice.imprenta_digital.save_factura(Dajax.process,
                                    {'form':$('#form_factura').serialize(true),
                                     'config_form':$('#form_crear_config').serialize(true),
                                     'customer_form':$('#form_crear_cliente').serialize(true)});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert("Seleccione al menos un producto a facturar.");
    }
    return false;
};

function generar_archivo_factura(factura_id,codigo_original) {
    
    if(codigo_original){
     bootbox.confirm(
        'ATENCIÓN: '+mensaje_comprobante+'',
        function(result) {
          if(result) {
              showWait();
               Dajaxice.imprenta_digital.generar_archivo_factura(Dajax.process,
                                           {'factura_id':factura_id});
            }
        });
        
    }else{
        bootbox.confirm(
        'ATENCIÓN:   Ha revisado la información de su comprobante y está seguro(a) de la misma para su procesamiento electrónico? Pulse OK para Continuar o Cancel para Cancelar.',
        function(result) {
            if(result) {
                showWait();
                Dajaxice.imprenta_digital.generar_archivo_factura(Dajax.process,
                                            {'factura_id':factura_id});
            }
        });
    }
    return false;
};

function save_factura_config() {
    Dajaxice.imprenta_digital.save_factura_config(Dajax.process,
                                {'form':$('#form_crear_config').serialize(true)});
    return false;
};

function clear_destinatario(obj) {
    $('#id_destinatario_1').val('');
    $('#id_destinatario_0').val('');
};


function new_destinatario() {
    var destinatario_id = $('#id_destinatario_1').val();
    showSmallWait();
    Dajaxice.imprenta_digital.bind_destinatario_form(Dajax.process,
                            {'destinatario_id':destinatario_id});
    return false;
};

function save_destinatario() {
    showWait();
    var destinatario_id = $('#id_id_registro_destinatario').val();
    var ruc= $('#id_id_registro_destinatario').val();
    Dajaxice.imprenta_digital.save_destinatario(Dajax.process,
                                {'form':$('#form_crear_destinatario').serialize(true),
                                 'destinatario_id':destinatario_id});
    return false;
};

function save_guia_remision() {
    var primer_producto_id = $('#id_impdgrproductodestinatario_set-0-producto_1').val();
    
    if(primer_producto_id) {
        showWait();
        Dajaxice.imprenta_digital.save_guia_remision(Dajax.process,
                                    {'form':$('#form_guia').serialize(true),
                                    'config_form':$('#form_crear_config').serialize(true),
                                    'detalle_destinatario_form':$('#form_detalle_destinatario').serialize(true),});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert("Seleccione al menos un producto a transportar.");
    }    
    return false;
};

/*
 * Nota Debito
 */

function save_nota_debito() {
    var codigo_impuesto = $('#id_impdnotadebitoimpuestos_set-0-codigo_impuesto').val();
    var motivo = $('#id_impdnotadebitomotivos_set-0-razon').val();
    if(codigo_impuesto && motivo) {
        showWait();
        Dajaxice.imprenta_digital.save_nota_debito(Dajax.process,
                                {'form':$('#form_notadebito').serialize(true),
                                 'config_form':$('#form_crear_config').serialize(true),
                                 'customer_form':$('#form_crear_cliente').serialize(true)});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert("Se requiere al menos un impuesto y un motivo de cambio.");
    }
    return false;
};

function generar_archivo_nota_debito(nota_debito_id,codigo_original) {
    if(codigo_original){
     bootbox.confirm(
        'ATENCIÓN: '+mensaje_comprobante+'',
        
        function(result) {
          if(result) {
              showWait();
               Dajaxice.imprenta_digital.generar_archivo_nota_debito(Dajax.process,
                                           {'nota_debito_id':nota_debito_id});
            }
        });
        
    }else{
        bootbox.confirm(
        'ATENCIÓN: Ha revisado la información de su comprobante y está seguro(a) de la misma para su procesamiento electrónico? Pulse OK para Continuar o Cancel para Cancelar.',
        function(result) {
            if(result) {
                showWait();
                Dajaxice.imprenta_digital.generar_archivo_nota_debito(Dajax.process,
                                {'nota_debito_id':nota_debito_id});
            }
        });}
    
    
    
    
    return false;
};

/*
 * Nota Debito - Fin
 */

function generar_archivo_guia(guia_id,codigo_original) {
    if(codigo_original){
     bootbox.confirm(
        'ATENCIÓN:  '+mensaje_comprobante+'',
        
        function(result) {
          if(result) {
              showWait();
               Dajaxice.imprenta_digital.generar_archivo_guia(Dajax.process,
                                           {'guia_id':guia_id});
            }
        });
        
    }else{
     bootbox.confirm(
        'ATENCIÓN: Ha revisado la información de su comprobante y está seguro(a) de la misma para su procesamiento electrónico? Pulse OK para Continuar o Cancel para Cancelar.',
        function(result) {
            if(result) {
                showWait();
                 Dajaxice.imprenta_digital.generar_archivo_guia(Dajax.process,
                                {'guia_id':guia_id});
            }
        });   
        
    }
    
    
    return false;
};

function save_retencion() {
    var impuesto = $('#id_impdcretimpuestos_set-0-codigo_impuesto').val();
    if(impuesto) {
        showWait();
        Dajaxice.imprenta_digital.save_retencion(Dajax.process,
                                    {'form':$('#form_retencion').serialize(true),
                                    'config_form':$('#form_crear_config').serialize(true),
                                    'customer_form':$('#form_crear_cliente').serialize(true)});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert('Es requerido agregar al menos un impuesto a la retención.');
    }
    return false;
};

function generar_archivo_retencion(retencion_id,codigo_original) {
    if(codigo_original){
     bootbox.confirm(
        'ATENCIÓN: '+mensaje_comprobante+'',
        
        function(result) {
          if(result) {
              showWait();
               Dajaxice.imprenta_digital.generar_archivo_retencion(Dajax.process,
                                           {'retencion_id':retencion_id});
            }
        });
        
    }else{
        bootbox.confirm(
        'ATENCIÓN: Ha revisado la información de su comprobante y está seguro(a) de la misma para su procesamiento electrónico? Pulse OK para Continuar o Cancel para Cancelar.',
        function(result) {
            if(result) {
                showWait();
                Dajaxice.imprenta_digital.generar_archivo_retencion(Dajax.process,
                                {'retencion_id':retencion_id});
            }
        });
    
        
    }
    return false;
    
    
    
};

/*function update_field(source, source_id, target) {
    //source_val = $('#'+source).val()
    //target_field_id = source.replace(source_id, target);
    //$('#'+target_field_id).val( parseInt(source_val) );
    //hideWait();
};*/



function update_field(source, source_id, target) {
    //alert(source);
    var id_item = $(source).attr('id');
    if (id_item === undefined) {
        alert(id_item);
        id_item = $('#'+source).attr('id');
     }
    console.log('ID: '+id_item);
    source_val = $('#'+id_item).val();
    console.log('Source: '+source_val);
    console.log('id_item: '+id_item+" -> "+source_id+" -> "+target );
    id_item = id_item.replace(source_id, target);
    console.log('Reemplazando '+id_item);
    
    $('#'+id_item).val( source_val ).change();
    console.log('Reemplazado! '+$('#'+id_item).val());
    hideWait();
};

function show_field(obj, target) {
    target_field_id = get_set_field_id(obj, target);
    $('#'+target_field_id).removeClass('input_hide');
    
};

function hide_field(obj, target) {
    target_field_id = get_set_field_id(obj, target);
    $('#'+target_field_id).addClass('input_hide');
};

function updateImpuestos(obj, target1, target2, cat_comun, cat_target1, cat_target2) {
    showWait();
    catalog_filter(obj, target1, cat_comun, cat_target1);
    setTimeout(function() {
        catalog_filter_extra(obj, target2, cat_comun, cat_target2);
    }, 100);
};

function clearForm(form_name) {
    $(':input','#'+form_name)
    .removeAttr('checked')
    .removeAttr('selected')
    .not(':button, :submit, :reset, :hidden, :radio, :checkbox')
    .val('');
};

function completeClearForm(form_name) {
    clearForm(form_name);
    $('#'+form_name+' input').removeClass('field_error');
    $('#'+form_name+' select').removeClass('field_error');
    $('.custom_error_list').html('');
};

function filter_impd_facturas() {
    Dajaxice.imprenta_digital.filter_impd_facturas(Dajax.process,
                                {'form':$('#search_factura').serialize(true)});
    return false;
};

function filter_impd_guias() {
    Dajaxice.imprenta_digital.filter_impd_guias(Dajax.process,
                                {'form':$('#search_guia').serialize(true)});
    return false;
};

function filter_impd_retenciones() {
    Dajaxice.imprenta_digital.filter_impd_retenciones(Dajax.process,
                                {'form':$('#search_retencion').serialize(true)});
    return false;
};

/*
 * NUEVO: NOTA DE CREDITO
 */

function filter_impd_notascredito() {
    Dajaxice.imprenta_digital.filter_impd_notascredito(Dajax.process,
                                {'form':$('#search_notacredito').serialize(true)});
    return false;
};

function save_nota_credito() {
    var producto = $('#id_impditemnotacredito_set-0-id_producto_1').val();
    if(producto) {
        showWait();
        Dajaxice.imprenta_digital.save_nota_credito(Dajax.process,
                                    {'form':$('#form_notacredito').serialize(true),
                                     'config_form':$('#form_crear_config').serialize(true),
                                     'customer_form':$('#form_crear_cliente').serialize(true)});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert('Es requerido seleccionar al menos un producto en la nota de crédito.');
    }
    return false;
};

function generar_archivo_nota_credito(nota_credito_id,codigo_original) {
    if(codigo_original){
     bootbox.confirm(
        'ATENCIÓN: '+mensaje_comprobante+'',
        
        function(result) {
          if(result) {
              showWait();
               Dajaxice.imprenta_digital.generar_archivo_nota_credito(Dajax.process,
                                           {'nota_credito_id':nota_credito_id});
            }
        });
        
    }else{
        bootbox.confirm(
        'ATENCIÓN: Ha revisado la información de su comprobante y está seguro(a) de la misma para su procesamiento electrónico? Pulse OK para Continuar o Cancel para Cancelar.',
        function(result) {
            if(result) {
                showWait();
                Dajaxice.imprenta_digital.generar_archivo_nota_credito(Dajax.process,
                                {'nota_credito_id':nota_credito_id});
            }
        });
    }
    return false;
};

function select_producto(product_id, input) {
    if($('#form_factura').length > 0) {
        recalc_factura();
     }
    else {
        recalc_nota_credito();
    }
    return false;
};

function select_producto_guia(product_id, input) {
    showSmallWait();
    var id_input = $(input).attr('id');
    id_input = '#'+id_input.replace('producto_0','');
     product_id = $(id_input+'producto_1').val();
    if(product_id) {
        Dajaxice.imprenta_digital.display_product_data(Dajax.process,
                                        {'product_id':product_id, 'id_input':id_input});
    }
    
    return false;
};

function recalc_factura(input, field_name) {
     showSmallWait();
    /*
    var id_input = $(input).attr('id');
    id_input = id_input.replace(field_name, '');
    recalc_factura_inside('#'+id_input)*/
    
    Dajaxice.imprenta_digital.recalc_factura(Dajax.process,
                                        {'form':$('#form_factura').serialize(true),
                                        'items':getFacturaItems() });
    
    return false;
};

function recalc_inside(id_input, form_name) {
    var product_id = $(id_input+'id_producto_1').val();
    if(product_id) {
        var cantidad = $(id_input+'cantidad').val();
        var descuento = $(id_input+'descuento').val();
        if(form_name == 'form_factura') {
            Dajaxice.imprenta_digital.recalc_factura(Dajax.process,
                                        {'form':$('#'+form_name).serialize(true),
                                         'product_id':product_id, 'id_input':id_input,
                                         'quantity':cantidad, 'discount':descuento
                                        });                            
        }
        else {
            Dajaxice.imprenta_digital.recalc_nota_credito(Dajax.process,
                                        {'form':$('#'+form_name).serialize(true),
                                         'product_id':product_id, 'id_input':id_input,
                                         'quantity':cantidad, 'discount':descuento
                                        });
        }
    }
    else {
        //console.log('No hay para '+id_input+'id_producto_1');
        $(id_input+'precio_unitario').val('0.0');
        $(id_input+'precio_total').val('0.0');
        if(form_name == 'form_factura') {
            Dajaxice.imprenta_digital.recalc_factura(Dajax.process,
                                        {'form':$('#'+form_name).serialize(true),
                                         'product_id':null, 'id_input':id_input,
                                         'quantity':null, 'discount':null
                                        });
        }
        else {
            Dajaxice.imprenta_digital.recalc_nota_credito(Dajax.process,
                                        {'form':$('#'+form_name).serialize(true),
                                         'product_id':null, 'id_input':id_input,
                                         'quantity':null, 'discount':null
                                        });
        }
    }
    return false;
};

function recalc_factura_inside(id_input) {
    return recalc_inside(id_input, 'form_factura');
};

function recalc_notacredito_inside(id_input) {
    return recalc_inside(id_input, 'form_notacredito');
};



function recalc_nota_credito(input, field_name) {
    showSmallWait();
     
    Dajaxice.imprenta_digital.recalc_nota_credito(Dajax.process,
                                        {'form':$('#form_nota_credito').serialize(true),
                                        'items':getNotaCreditoItems()});
    return false;
};

/*
 * NUEVO-FIN: NOTA DE CREDITO
 */

function filter_impd_notasdebito() {
    Dajaxice.imprenta_digital.filter_impd_notasdebito(Dajax.process,
                                {'form':$('#search_notadebito').serialize(true)});
    return false;
};

function printIt() {
    var doc = new jsPDF();
    var source = $('#nuevo_comprobante').html();
    var specialElementHandlers = {
        '#bypassme': function (element, renderer) {
            console.log(element);
            return true;
        }
    };
    doc.fromHTML(source, 0.5, 0.5, {
        'width': 75,'elementHandlers': specialElementHandlers
    });
    doc.output("dataurlnewwindow");
    
    return false;
};

function getFacturaItems() {
    var formCount = parseInt($('#id_impditemfactura_set-TOTAL_FORMS').val());
    var items = [];
    
    for(i=0; i<formCount; i++) {
        cantidad =  $("#id_impditemfactura_set-"+i+"-cantidad" ).val();
        if(!cantidad || cantidad=='') {
            cantidad = 0;
            $("#id_impditemfactura_set-"+i+"-cantidad" ).val(cantidad)
        }
        descuento =  $("#id_impditemfactura_set-"+i+"-descuento" ).val();
        if(!descuento || descuento=='') {
            descuento = 0;
            $("#id_impditemfactura_set-"+i+"-descuento" ).val(descuento)
        }
        item = {
                cantidad: cantidad,
                producto: $( "#id_impditemfactura_set-"+i+"-id_producto_1" ).val(),
                descuento: descuento,
                input_id: "#id_impditemfactura_set-"+i+"-"
            };
        //console.log(item);
        items.push(item);
    }
    return items;
};

function getNotaCreditoItems() {
    var formCount = parseInt($('#id_impditemnotacredito_set-TOTAL_FORMS').val());
    var items = [];
    
    
    for(i=0; i<formCount; i++) {
        cantidad =  $("#id_impditemnotacredito_set-"+i+"-cantidad" ).val();
        if(!cantidad || cantidad=='') {
            cantidad = 0;
            $("#id_impditemnotacredito_set-"+i+"-cantidad" ).val(cantidad)
        }
        
        descuento = $("#id_impditemnotacredito_set-"+i+"-descuento" ).val();
        if(!descuento || descuento=='') {
            descuento = 0;
            $("#id_impditemnotacredito_set-"+i+"-descuento" ).val(descuento)
        }
        
        item = {
                cantidad: cantidad,
                producto: $( "#id_impditemnotacredito_set-"+i+"-id_producto_1" ).val(),
                descuento: descuento,
                input_id: "#id_impditemnotacredito_set-"+i+"-"
            };
        //console.log(item);
        items.push(item);
    }
    return items;
};

/*
 * UPDATES
 */

function update_factura() {
    var producto_id = $('#id_impditemfactura_set-0-id_producto_1').val();
                                      
    
    if(producto_id) {
        showWait();
        Dajaxice.imprenta_digital.update_factura(Dajax.process,
                                    {'form':$('#form_factura').serialize(true),
                                     'config_form':$('#form_crear_config').serialize(true),
                                     'customer_form':$('#form_crear_cliente').serialize(true)});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert("Seleccione al menos un producto a facturar.");
    }
    return false;
};

function update_guia_remision() {
    var primer_producto_id = $('#id_impdgrproductodestinatario_set-0-producto_1').val();
    if(primer_producto_id) {
        showWait();
        Dajaxice.imprenta_digital.update_guia_remision(Dajax.process,
                                    {'form':$('#form_guia').serialize(true),
                                     'config_form':$('#form_crear_config').serialize(true),
                                     'detalle_destinatario_form':$('#form_detalle_destinatario').serialize(true)});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert("Seleccione al menos un producto a transportar.");
    }
    return false;
};

function update_retencion() {
    var impuesto = $('#id_impdcretimpuestos_set-0-codigo_impuesto').val();
    if(impuesto) {
        showWait();
        Dajaxice.imprenta_digital.update_retencion(Dajax.process,
                                    {'form':$('#form_retencion').serialize(true),
                                    'config_form':$('#form_crear_config').serialize(true),
                                    'customer_form':$('#form_crear_cliente').serialize(true)});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert('Es requerido agregar al menos un impuesto a la retención.');
    }
    return false;
};

function update_nota_credito() {
    var producto = $('#id_impditemnotacredito_set-0-id_producto_1').val();
    if(producto) {
        showWait();
        Dajaxice.imprenta_digital.update_nota_credito(Dajax.process,
                                    {'form':$('#form_notacredito').serialize(true),
                                     'config_form':$('#form_crear_config').serialize(true),
                                     'customer_form':$('#form_crear_cliente').serialize(true)});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert('Es requerido seleccionar al menos un producto en la nota de crédito.');
    }
};

function update_nota_debito() {
    var codigo_impuesto = $('#id_impdnotadebitoimpuestos_set-0-codigo_impuesto').val();
    var motivo = $('#id_impdnotadebitomotivos_set-0-razon').val();
    if(codigo_impuesto && motivo) {
        showWait();
        Dajaxice.imprenta_digital.update_nota_debito(Dajax.process,
                                {'form':$('#form_notadebito').serialize(true),
                                 'config_form':$('#form_crear_config').serialize(true),
                                 'customer_form':$('#form_crear_cliente').serialize(true)});
        setTimeout(function(){hideWait();}, 2500);
    }
    else {
        bootbox.alert("Se requiere al menos un impuesto y un motivo de cambio.");
    }
    return false;
};

function delete_entity(tipo, id) {   
     Dajaxice.imprenta_digital.delete_entity(Dajax.process,
                                       {'tipo':tipo,
                                         'id':id});    
    return false;
};

function add_special_ruc(modo) {
    showSmallWait();
    if(modo == 1) {
        Dajaxice.imprenta_digital.add_special_ruc(Dajax.process, {'ruc':$('#id_identificacion').val()});
    }
    else if(modo == 2) {
        Dajaxice.imprenta_digital.add_special_ruc(Dajax.process, {'ruc':$('#id_identificacion_destinatario').val()});
    }
    else {
        Dajaxice.imprenta_digital.add_special_ruc(Dajax.process, {'ruc':$('#id_ruc_transportista').val()});
    }
    return false;
};

function anular_comprobante(tipo, id) {
    
    bootbox.dialog({
      title: TITULO_ANULACION_COMPROBANTE_DIGITAL,
      message:  '<div class="row"> ' +
      '<div class="col-md-12"> ' +
      '<p>'+MENSAJE_ANULACION_COMPROBANTE_DIGITAL+'</p>' +
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
                  window.location = '/imprenta-digital/comprobante/'+tipo+'/'+id+'/'+codigo+'/anular/';
               }
               else {
                  bootbox.alert(MENSAJE_ERROR_INGRESO_CODIGO);
               }
               
            }
         }
      }
    });

    return false;
};

function anular_factura(tipo, id) {
    
    bootbox.dialog({
      title: TITULO_ANULACION_COMPROBANTE_DIGITAL,
      message:  '<div class="row"> ' +
      '<div class="col-md-12"> ' +
      '<p>'+MENSAJE_ANULACION_COMPROBANTE_DIGITAL+'</p>' +
      '<form class="form-horizontal"> ' +
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
               var clave_acceso_nc = $('#clave_acceso_nc').val();
               var numero_autorizacion = $('#numero_autorizacion').val();
               if(clave_acceso_nc && clave_acceso_nc.length == 49 && numero_autorizacion && numero_autorizacion.length == 37 ) {
                  window.location = '/imprenta-digital/comprobante/'+tipo+'/'+id+'/'+clave_acceso_nc+'-'+numero_autorizacion+'/anular/';
                
               }
               else {
                  bootbox.alert(MENSAJE_ERROR_INGRESO_CODIGO_FACT);
               }
               
            }
         }
      }
    });

    return false;
};

function get_impuestos_reembolso(prefix_index) {
    showWait();
    Dajaxice.imprenta_digital.get_impuestos_reembolso(Dajax.process, {'item_prefix':prefix_index});
    return false;
};

function save_detalle_imp_reemb() {
    showWait();
    Dajaxice.imprenta_digital.add_impuestos_reembolso(Dajax.process,
                                {'form_impuestos_reembolso':$('#form_crear_imp_reem').serialize(true)});
    //setTimeout(function(){hideWait();}, 2500);
    return false;
};

function openImpReembolsoModal() {
    $('#button-modal-imp-reem').click();
};

function closeImpReembolsoModal() {
    $("#button-cerrar-modal-imp-reem").click();
};
