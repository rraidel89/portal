#import simplejson
from itertools import product
from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from dajaxice.core import dajaxice_functions

from django.template.loader import render_to_string
from django.utils import simplejson
from dajaxice.utils import deserialize_form
from django.template.context import RequestContext
from django.db.models.query_utils import Q

from django.db import IntegrityError

from core.validators import doc_validator
from core import mixins
import models
import forms
import traceback
import helpers
import json

def search_product(request, producto):
    productos_json = []
    if producto:
        print 'search_product - Buscando', producto
        productos = models.ImpdProducto.objects.filter(Q(descripcion__icontains = producto) |
                                                       Q(codigo_principal__icontains = producto) |
                                                       Q(codigo_secundario__icontains = producto))
        print 'search_product - Encontrados', productos.count(), 'elementos'
        for producto in productos:
            productos_json.append({
                'value' : producto.id,
                'label' : producto.descripcion
            })
    else:
        print 'search_product - No se ha dado un dato de busqueda'
    return simplejson.dumps(productos_json)

dajaxice_functions.register(search_product)

def search_customer(request, cliente):
    clientes_json = []
    if cliente:
        print 'search_customer - Buscando', cliente
        clientes = models.ImpdCliente.objects.filter(Q(identificacion__icontains = cliente) | Q(razon_social__icontains = cliente))
        print 'search_customer - Encontrados', clientes.count(), 'elementos'
        for cliente in clientes:
            clientes_json.append({
                'value' : cliente.id,
                'label' : cliente.razon_social
            })
    else:
        print 'search_customer - No se ha dado un dato de busqueda'
    return simplejson.dumps(clientes_json)

dajaxice_functions.register(search_customer)

def search_customer_inline(request, tipo_identificacion, identificacion, ruc_empresa):
    dajax = Dajax()
    if tipo_identificacion and identificacion:
        print 'search_customer - Buscando', tipo_identificacion, identificacion, ruc_empresa
        clientes = models.ImpdCliente.objects.filter(tipo_identificacion = tipo_identificacion,
                                                     identificacion = identificacion,
                                                     ruc_empresa = ruc_empresa)
        print 'cantidad',clientes.count()
        if clientes.count() > 0:
            cliente = clientes[0]
            dajax.assign('#id_razon_social', 'value', cliente.razon_social)
            dajax.assign('#id_email_principal', 'value', cliente.email_principal)
            dajax.assign('#id_email_secundario', 'value', cliente.email_secundario)
            dajax.assign('#id_direccion_comprador', 'value', cliente.direccion_comprador)
        else:
            dajax.script('bootbox.alert("No se encontraron clientes con esos datos.");')
    else:
        print 'search_customer - No se ha dado un dato de busqueda'
        dajax.script('bootbox.alert("Es necesario el tipo de identificacion y la identificacion.");')
    dajax.script('hideSmallWait();')
    return dajax.json()

dajaxice_functions.register(search_customer_inline)

def search_customer_inline_GR(request, tipo_identif_transportista, ruc_empresa,ruc_transportista):
    dajax = Dajax()
    if tipo_identif_transportista and ruc_transportista:
        print 'search_customer - Buscando', tipo_identif_transportista
        transportista = models.ImpdGuiaRemision.objects.filter(tipo_identif_transportista = tipo_identif_transportista, ruc_empresa = ruc_empresa,ruc_transportista=ruc_transportista)
        if transportista.count() > 0:
            transportista = transportista[0]
            dajax.assign('#id_direccion_partida', 'value', transportista.direccion_partida)
            dajax.assign('#id_razon_social_transportista', 'value', transportista.razon_social_transportista)
            dajax.assign('#id_rise', 'value', transportista.rise)
            dajax.assign('#id_placa', 'value', transportista.placa)
            
        else:
            dajax.script('bootbox.alert("No se encontraron transportista con esos datos.");')
    else:
        print 'search_customer - No se ha dado un dato de busqueda'
        dajax.script('bootbox.alert("Es necesario el tipo de identificacion y la identificacion.");')
    dajax.script('hideSmallWait();')
    return dajax.json()

dajaxice_functions.register(search_customer_inline_GR)

def delete_entity(request, tipo, id):
    dajax = Dajax()

    print '==> ELIMINANDO ELEMENTO', tipo, id
    
    if tipo=='item-info-adi_impdfacturainformacionadicional_set':
     entity = models.ImpdFacturaInformacionAdicional.objects.get(pk=id)
     entity.delete()
     
    if tipo=='item_factura': 
     entity = models.ImpdItemFactura.objects.get(pk=id)
     entity.delete()
     
    if tipo=='item-gr-prod': 
      entity = models.ImpdGRProductoDestinatario.objects.get(pk=id)
      entity.delete()
     
    if tipo=='item-info-adi_impdgrinformacionadicional_set': 
      entity = models.ImpdGRInformacionAdicional.objects.get(pk=id)
      entity.delete()
      
    if tipo=='item_retencion_impuesto': 
      entity = models.ImpdGRInformacionAdicional.objects.get(pk=id)
      entity.delete()
     
    if tipo=='item_nota_credito': 
      entity = models.ImpdItemNotaCredito.objects.get(pk=id)
      entity.delete()
      
    if tipo=='item-info-adi_impdnotacreditoinformacionadicional_set': 
      entity = models.ImpdNotaCreditoInformacionAdicional.objects.get(pk=id)
      entity.delete()
      
    if tipo=='item_nota_debito_impuesto': 
      entity = models.ImpdNotaDebitoImpuestos.objects.get(pk=id)
      entity.delete()
      
    if tipo=='item_nota_debito_motivos': 
      entity = models.ImpdNotaDebitoMotivos.objects.get(pk=id)
      entity.delete()
      
    if tipo=='item-info-adi_impdnotadebitoinfoadicional_set': 
      entity = models.ImpdNotaDebitoInfoAdicional.objects.get(pk=id)
      entity.delete()
      
    if tipo=='item_det_prod_detalles_adicionales': 
      entity = models.ImpdProductoDetalleAdicional .objects.get(pk=id)
      entity.delete()
      
    if tipo=='item_imp_prod_impuestos': 
      entity = models.ImpdProductoImpuesto .objects.get(pk=id)
      entity.delete()
      
    if tipo=='item_impuesto_retencion': 
      entity = models.ImpdCRETImpuestos .objects.get(pk=id)
      entity.delete()
      
    if tipo=='item-reembolso':
      entity = models.ImpdFactReembolso.objects.get(pk=id)
      imp_reem = models.ImpdFactDetalleImpuestoReembolso.objects.filter(reembolso = entity)
      for irem in imp_reem:
          irem.delete()
      entity.delete()

    if tipo=='item-pago':
      entity = models.ImpdFactPago.objects.get(pk=id)
      entity.delete()


    return dajax.json()

dajaxice_functions.register(delete_entity)

def save_customer(request, form):
    dajax = Dajax()
    try:
        print 'Guardando cliente...'
        form = forms.ClienteForm(deserialize_form(form))
        if form.is_valid():
            print 'Formulario Valido'
            entity = form.save(commit=False)
            entity.ruc_empresa = request.user.get_profile().ruc_empresa
            entity.save(user = request.user)
            dajax.assign('#crear_cliente_error_list', 'innerHTML', '')
            dajax.remove_css_class('#form_crear_cliente input', 'field_error')
            dajax.script("$('#close-modal-crear-cliente').click();");
            dajax.assign('#id_id_cliente_0', 'value', '%s' % entity.razon_social)
            dajax.assign('#id_id_cliente_1', 'value', '%s' % entity.id)
            dajax.script('clearForm("form_crear_cliente");')
        else:
            dajax.assign('#crear_cliente_error_list', 'innerHTML', '')
            dajax.assign('#form_crear_cliente .errors_list_custom', 'innerHTML', '')
            for error in form.errors:
                dajax.add_css_class('#id_%s' % error, 'field_error')
                
            html = render_to_string('emisores/imprenta_digital/messages.html', {'form': form})
            dajax.assign('#crear_cliente_error_list', 'innerHTML', html)
    except IntegrityError as e:
        dajax.alert("Error: un usuario con esas caracteristicas ya existe.")
    except Exception as e:
        dajax.alert("save_customer - Error: %s" % str(e))
        traceback.print_exc()
    return dajax.json()

dajaxice_functions.register(save_customer)

def save_product(request, form, product_id=None):
    dajax = Dajax()
    try:
        print 'Guardando producto', product_id
        des_form = deserialize_form(form)
        
        if product_id:
            producto = models.ImpdProducto.objects.get(pk = product_id)
        else:
            producto = models.ImpdProducto()
        
        form = forms.ProductoForm(des_form, instance = producto)
        detalle_adicional_producto_form = forms.ProductoDetalleAdicionalFormSet(des_form, instance = producto)
        impuesto_producto_form = forms.ProductoImpuestoFormSet(des_form, instance = producto)
        
        if (form.is_valid() and detalle_adicional_producto_form.is_valid()) and impuesto_producto_form.is_valid():
            entity = form.save(commit=False)
            entity.ruc_empresa = request.user.get_profile().ruc_empresa
            entity.save(user = request.user)

            detalle_adicional_producto_form.instance = entity
            detalle_adicional_producto_form.save()

            impuesto_producto_form.instance = entity
            impuesto_producto_form.save()

            dajax.remove_css_class('#form_crear_producto input', 'field_error')
            dajax.script("$('#close-modal-crear-producto').click();");
            dajax.assign(form.get_name(), 'value', '%s' % entity.descripcion)
            dajax.assign(form.get_name_id(), 'value', '%s' % str(entity.id))
            name = form.get_name_id().replace('id_producto_1', '')
            dajax.script("recalc('%s');" % name);
            dajax.script('clearForm("form_crear_producto");')
            print 'Producto Guardado'
        else:
            dajax.assign('#crear_producto_error_list', 'innerHTML', '')
            dajax.remove_css_class('body input', 'field_error')

            set_form_errors(dajax, form)
            set_formset_errors(dajax, detalle_adicional_producto_form)
            set_formset_errors(dajax, impuesto_producto_form)

            html = render_to_string('emisores/imprenta_digital/messages.html', {'form': form,
                                                                                'formset1':detalle_adicional_producto_form,
                                                                                'formset2':impuesto_producto_form})
            dajax.assign('#crear_producto_error_list', 'innerHTML', html)
    except Exception as e:
        dajax.alert("save_product - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(save_product)

def set_form_errors(dajax, form):
    for error in form.errors:
        dajax.add_css_class('#id_%s' % error, 'field_error')

def set_formset_errors(dajax, form):
    for error in form.errors:
        for field in error:
            print 'F', field
            dajax.add_css_class('#id_%s' % field, 'field_error')

def save_factura(request, form, config_form, customer_form):
    dajax = Dajax()
    try:
        print 'GUARDANDO FACTURA'
        des_form = deserialize_form(form)
        form = forms.FacturaForm(request, des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa})
        item_factura_form = forms.ItemFacturaFormSet(request.user.get_profile().ruc_empresa, des_form)
        info_adicional_form = forms.InformacionAdicionalFormSet(des_form)
        info_adicional_form = forms.InformacionAdicionalFormSet(des_form)
        config_form = forms.ConfiguracionFacturaForm(deserialize_form(config_form))
        customer_form = forms.ClienteForm(deserialize_form(customer_form))
        valid_reembolsos = True
        reembolso_factura_form = None
        valid_pagos = True
        pago_factura_form = None

        profile = request.user.get_profile()
        if profile.ruc_empresa.reembolsos:
            reembolso_factura_form = forms.ReembolsosFormSet(des_form)
            valid_reembolsos = reembolso_factura_form.is_valid()
            pago_factura_form = forms.PagoFormSet(des_form)
            valid_pagos = pago_factura_form.is_valid()

        if (form.is_valid() and item_factura_form.is_valid()
            and info_adicional_form.is_valid() and config_form.is_valid() and customer_form.is_valid()
            and valid_reembolsos and valid_pagos):
            helper = helpers.IMPDFacturaHelper(request, item_factura_form, form, info_adicional_form,
                                               reembolso_factura_form, pago_factura_form)
            save_all_helper = helpers.SaveAllHelper(dajax, 'factura', 'facturas', helper)
            dajax.script('bootbox.alert("DOCUMENTO GUARDADO");')
            return save_all_helper.saveAll(form, config_form, customer_form, item_factura_form,
                                           info_adicional_form, reembolso_factura_form, pago_factura_form)
        else:
            save_all_helper = helpers.SaveAllHelper(dajax, 'factura', 'facturas')
            return save_all_helper.manage_errors(form, config_form, customer_form, item_factura_form,
                                                 info_adicional_form, reembolso_factura_form, pago_factura_form)
    except Exception as e:
        dajax.alert("save_factura - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(save_factura)

def update_factura(request, form, config_form, customer_form):
    dajax = Dajax()
    
    try:
        updated_entity = request.session['updated-entity']
        des_form = deserialize_form(form)
        if updated_entity:            
            form = forms.FacturaForm(request, des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa},
                                     instance=updated_entity)
            item_factura_form = forms.ItemFacturaFormSet(request.user.get_profile().ruc_empresa, des_form,
                                                         instance=updated_entity)
            info_adicional_form = forms.InformacionAdicionalFormSet(des_form, instance=updated_entity)
            customer_form = forms.ClienteForm(deserialize_form(customer_form),
                                              initial={'ruc_empresa': request.user.get_profile().ruc_empresa},
                                              instance=updated_entity.id_cliente)
            valid_reembolsos = True
            reembolso_factura_form = None
            valid_pagos = True
            pago_factura_form = None

            profile = request.user.get_profile()
            if profile.ruc_empresa.reembolsos:
                reembolso_factura_form = forms.ReembolsosFormSet(des_form, instance=updated_entity)
                valid_reembolsos = reembolso_factura_form.is_valid()
                pago_factura_form = forms.PagoFormSet(des_form, instance=updated_entity)
                valid_pagos = pago_factura_form.is_valid()

            if (form.is_valid() and item_factura_form.is_valid() and info_adicional_form.is_valid() and
                customer_form.is_valid() and valid_reembolsos and valid_pagos):
                customer = customer_form.save()
                entity = form.save(id_cliente=customer, commit=True)
                entity.save()
                item_factura_form.instance = entity
                item_factura_form.save()
                info_adicional_form.instance = entity
                info_adicional_form.save()

                if reembolso_factura_form:
                    reembolso_factura_form.instance = entity
                    reembolso_factura_form.save()

                if pago_factura_form:
                    pago_factura_form.instance = entity
                    pago_factura_form.save()

                helper = helpers.IMPDFacturaHelper(request, item_factura_form, form)
                helper.update(entity)

                if reembolso_factura_form:
                    helper.save_imp_reem(reembolso_factura_form)

                save_all_helper = helpers.SaveAllHelper(dajax, 'factura', 'facturas')
                dajax.script('bootbox.alert("DOCUMENTO ACTUALIZADO");')
                return save_all_helper.ajax_response()
            else:
                save_all_helper = helpers.SaveAllHelper(dajax, 'factura', 'facturas')
                return save_all_helper.manage_errors(form, None, customer_form, item_factura_form, info_adicional_form,
                                                     reembolso_factura_form, pago_factura_form)
    except Exception as e:
        dajax.alert("update_factura - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(update_factura)

def recalc_factura(request, form, items):
    dajax = Dajax()
    try:
        impuestos = 0
        descuentos = 0
        total_sin_impuestos = 0
        total_con_impuestos = 0
        for item in items:
            if item['producto']:
                print '--> ITEM', item
                producto = models.ImpdProducto.objects.get(pk = item['producto'])
                subtotal = float(item['cantidad']) * float(producto.precio_unitario) - float(item['descuento'])
                print '--> TOTAL', subtotal
                dajax.assign(item['input_id']+'precio_unitario', 'value', str(producto.precio_unitario))
                dajax.assign(item['input_id']+'precio_total', 'value', str(subtotal))
                impuestos_producto = float(producto.get_impuestos(subtotal))
                impuestos += impuestos_producto
                print 'Impuestos', impuestos_producto
                descuentos += float(item['descuento'])
                total_sin_impuestos += float(subtotal)
                total_con_impuestos += float(subtotal + impuestos_producto)
                print '------------', total_con_impuestos
            
        html = render_to_string('emisores/imprenta_digital/factura/totales-factura.html', {
            'total_sin_impuestos': total_sin_impuestos,
            'total_con_impuestos': total_con_impuestos,
            'total_descuentos': descuentos,
            'total_impuestos': impuestos})
        dajax.assign('#widget-totales-factura', 'innerHTML', html)
        
        try:
            updated_entity = request.session['updated-entity']
        except:
            updated_entity = None

        des_form = deserialize_form(form)
        if updated_entity:
            form = forms.FacturaForm(request, des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa}, instance=updated_entity)
            item_factura_form = forms.ItemFacturaFormSet(request.user.get_profile().ruc_empresa, des_form, instance=updated_entity)
        else:
            form = forms.FacturaForm(request, des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa})
            item_factura_form = forms.ItemFacturaFormSet(request.user.get_profile().ruc_empresa, des_form)
        form.is_valid()
        item_factura_form.is_valid()
        print 'OK'
    except Exception as e:
        print "recalc_factura - Error: %s" % str(e)
        traceback.print_exc()
    dajax.script('hideSmallWait();')
    return dajax.json()

dajaxice_functions.register(recalc_factura)

def generar_archivo_factura(request, factura_id):
    dajax = Dajax()
    try:
        helper = helpers.IMPDFacturaHelper(request)
        factura = helper.generar_archivo(factura_id)
        dajax.script('bootbox.alert("FACTURA %s generada con exito. En unos minutos se procede a su AUTORIZACION.");' % factura.codigo_original)
        dajax.script("window.location = '/imprenta-digital/facturas/';");
        dajax.script('hideWait();')
    except Exception as e:
        dajax.alert("Error al Generar archivo para FACTURA: %s" % str(e))
        traceback.print_exc()
        dajax.script('hideWait();')
        dajax.script("window.location = '/imprenta-digital/facturas/';");
    return dajax.json()

dajaxice_functions.register(generar_archivo_factura)

def catalog_filter(request, catalog_value, catalog_module, source_module=None, to_decimal=False):
    catalogos = []
    if catalog_value and catalog_module:
        print 'catalog_filter - Filtrando', catalog_module, catalog_value, source_module, to_decimal
        catalogos = helpers.catalogo_helper.get_catalogos_dependientes(catalog_module, catalog_value, source_module, to_decimal)
        print 'catalog_filter - Encontrados', len(catalogos), 'elementos', catalogos
    else:
        print 'catalog_filter - No se ha dado un dato de filtro'
    return simplejson.dumps(catalogos)

dajaxice_functions.register(catalog_filter)

def save_factura_config(request, form):
    dajax = Dajax()
    try:
        print 'Guardando configuracion...', request
        form = forms.ConfiguracionFacturaForm(deserialize_form(form))
        if form.is_valid():
            print 'Formulario Valido'
            entity = form.save(commit=False)
            entity.ruc_empresa = request.user.get_profile().ruc_empresa
            entity.save(user = request.user)
            dajax.assign('#crear_configuracion_error_list', 'innerHTML', '')
            dajax.remove_css_class('#form_crear_config input', 'field_error')
            dajax.script("$('#close-modal-crear-configuracion').click();");
            dajax.assign('#id_id_configuracion_0', 'value', '%s' % entity.descripcion)
            dajax.assign('#id_id_configuracion_1', 'value', '%s' % entity.id)
            dajax.assign('#id_id_configuracion', 'value', '%s' % entity.id)
            dajax.script('clearForm("form_crear_config");')
        else:
            dajax.assign('#crear_configuracion_error_list', 'innerHTML', '')
            dajax.assign('#form_crear_config .errors_list_custom', 'innerHTML', '')
            for error in form.errors:
                dajax.add_css_class('#id_%s' % error, 'field_error')
                
            html = render_to_string('emisores/imprenta_digital/messages.html', {'form': form})
            dajax.assign('#crear_configuracion_error_list', 'innerHTML', html)
    except Exception as e:
        dajax.alert("save_factura_config - Error: %s" % str(e))
        traceback.print_exc()
    return dajax.json()

dajaxice_functions.register(save_factura_config)

'''
---------------------------------
GUIAS DE REMISION
---------------------------------
'''

def save_destinatario(request, form, destinatario_id):
    dajax = Dajax()
    try:
        print 'Guardando destinatario', destinatario_id
        if destinatario_id:
            destinatario = models.ImpdGRDestinatario.objects.get(pk = destinatario_id)
        else:
            destinatario = models.ImpdGRDestinatario()
        
        des_form = deserialize_form(form)
        form = forms.ImpdDestinatarioForm(des_form, instance=destinatario)
        if form.is_valid():
            entity = form.save(commit=False)
            entity.ruc_empresa = request.user.get_profile().ruc_empresa
            entity.save(user = request.user)
            
            dajax.remove_css_class('#form_crear_destinatario input', 'field_error')
            dajax.script("$('#close-modal-crear-destinatario').click();");
            dajax.assign('#id_destinatario_0', 'value', '%s' % entity.get_descripcion())
            dajax.assign('#id_destinatario_1', 'value', '%s' % str(entity.id))
            dajax.script('clearForm("form_crear_destinatario");')
        else:
            dajax.assign('#crear_destinatario_error_list', 'innerHTML', '')
            dajax.remove_css_class('#form_crear_destinatario input', 'field_error')

            for error in form.errors:
                dajax.add_css_class('#id_%s' % error, 'field_error')
            
            html = render_to_string('emisores/imprenta_digital/messages.html', {'form': form})
            dajax.assign('#crear_destinatario_error_list', 'innerHTML', html)
            
    except Exception as e:
        dajax.alert("save_destinatario - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(save_destinatario)

def save_guia_remision(request, form, config_form, detalle_destinatario_form):
    dajax = Dajax()
    try:
        des_form = deserialize_form(form)
        form = forms.GuiaRemisionForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa})
        detalle_destinatario_form_des = deserialize_form(detalle_destinatario_form)
        detalle_dest_form = forms.ImpdGuiaRemisionDetalleDestinatarioForm(request.user.get_profile().ruc_empresa,
                                                                                  detalle_destinatario_form_des)
        productos_detalle_destinatario_form = forms.ImpdGuiaRemisionProductoDestinatarioFormSet(request.user.get_profile().ruc_empresa,
                                                                                  detalle_destinatario_form_des)
        info_adicional_form = forms.InformacionAdicionalGuiaRemisionFormSet(des_form)
        config_form = forms.ConfiguracionFacturaForm(deserialize_form(config_form))
        if (form.is_valid() and detalle_dest_form.is_valid() and productos_detalle_destinatario_form.is_valid() and
            info_adicional_form.is_valid() and config_form.is_valid()):
            helper = helpers.IMPDGuiaRemisionHelper(request, detalle_dest_form, productos_detalle_destinatario_form, info_adicional_form)
            save_all_helper = helpers.SaveAllHelper(dajax, 'guia', 'guiasremision', helper)
            dajax.script('bootbox.alert("DOCUMENTO GUARDADO");')
            return save_all_helper.saveAll(form, config_form, None, info_adicional_form)
        else:
            save_all_helper = helpers.SaveAllHelper(dajax, 'guia', 'guiasremision')
            return save_all_helper.manage_errors(form, config_form, detalle_dest_form, productos_detalle_destinatario_form, info_adicional_form)

     
    except Exception as e:
        dajax.alert("save_guia_remision - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(save_guia_remision)

def update_guia_remision(request, form, config_form, detalle_destinatario_form):
    dajax = Dajax()
    try:
        updated_entity = request.session['updated-entity']
        des_form = deserialize_form(form)
        if updated_entity:            
            
            form = forms.GuiaRemisionForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa}, instance = updated_entity)
            detalle_destinatario_form_des = deserialize_form(detalle_destinatario_form)
            destinatario_entity = updated_entity.get_destinatarios()[0]
            detalle_dest_form = forms.ImpdGuiaRemisionDetalleDestinatarioForm(request.user.get_profile().ruc_empresa,
                                                                            detalle_destinatario_form_des, instance = destinatario_entity)
            productos_detalle_destinatario_form = forms.ImpdGuiaRemisionProductoDestinatarioFormSet(request.user.get_profile().ruc_empresa,
                                                                            detalle_destinatario_form_des, instance = destinatario_entity)
            info_adicional_form = forms.InformacionAdicionalGuiaRemisionFormSet(des_form, instance = updated_entity)
            
            if form.is_valid() and detalle_dest_form.is_valid() and productos_detalle_destinatario_form.is_valid() and info_adicional_form.is_valid():
                entity = form.save(commit=False)
                entity.save()
                detalle_dest_form.guia_remision = entity
                detalle_dest = detalle_dest_form.save(entity)
                productos_detalle_destinatario_form.instance = detalle_dest
                productos_detalle_destinatario_form.save()                
                info_adicional_form.instance = entity
                info_adicional_form.save()
                
                helper = helpers.IMPDGuiaRemisionHelper(request, detalle_dest_form, productos_detalle_destinatario_form, info_adicional_form)
                helper.update(entity)
                save_all_helper = helpers.SaveAllHelper(dajax, 'guia', 'guiasremision', helper)
                dajax.script('bootbox.alert("DOCUMENTO ACTUALIZADO");')
                return save_all_helper.ajax_response()
            else:
                save_all_helper = helpers.SaveAllHelper(dajax, 'guia', 'guiasremision')
                return save_all_helper.manage_errors(form, None, detalle_dest_form, productos_detalle_destinatario_form, info_adicional_form)
    except Exception as e:
        dajax.alert("update_guia_remision - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(update_guia_remision)

def generar_archivo_guia(request, guia_id):
    dajax = Dajax()
    try:
        helper = helpers.IMPDGuiaRemisionHelper(request)
        guia = helper.generar_archivo(guia_id)
        dajax.script('bootbox.alert("GUIA DE REMISION %s generada con exito. En unos minutos se procede a su AUTORIZACION");' % guia.secuencial)
    except Exception as e:
        dajax.alert("Error al Generar archivo para GUIA DE REMISION: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    dajax.script("window.location = '/imprenta-digital/guiasremision/';");
    return dajax.json()

dajaxice_functions.register(generar_archivo_guia)

'''
---------------------------------
COMPROBANTES DE RETENCION
---------------------------------
'''

def save_retencion(request, form, config_form, customer_form):
    dajax = Dajax()
    try:
        des_form = deserialize_form(form)
        form = forms.ComproRetencionForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa})
        impuestos_form = forms.ImpdCRETImpuestosFormSet(des_form)
        info_adicional_form = forms.InformacionAdicionalCRETFormSet(des_form)
        config_form = forms.ConfiguracionFacturaForm(deserialize_form(config_form))
        customer_form = forms.ClienteForm(deserialize_form(customer_form))
        if (form.is_valid() and impuestos_form.is_valid() and info_adicional_form.is_valid() and
            config_form.is_valid() and customer_form.is_valid()):
            helper = helpers.IMPDComprobanteRetencionHelper(request, impuestos_form, info_adicional_form)
            save_all_helper = helpers.SaveAllHelper(dajax, 'retencion', 'retenciones', helper)
            dajax.script('bootbox.alert("DOCUMENTO GUARDADO");')
            return save_all_helper.saveAll(form, config_form, customer_form, impuestos_form, info_adicional_form)
        else:
            save_all_helper = helpers.SaveAllHelper(dajax, 'retencion', 'retenciones')
            return save_all_helper.manage_errors(form, config_form, customer_form, impuestos_form, info_adicional_form)
    except Exception as e:
        dajax.alert("save_retencion - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(save_retencion)

def update_retencion(request, form, config_form, customer_form):
    dajax = Dajax()
    try:
        updated_entity = request.session['updated-entity']
        des_form = deserialize_form(form)
        if updated_entity:            
            form = forms.ComproRetencionForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa}, instance=updated_entity)
            impuestos_form = forms.ImpdCRETImpuestosFormSet(des_form, instance=updated_entity)
            info_adicional_form = forms.InformacionAdicionalCRETFormSet(des_form, instance=updated_entity)
            customer_form = forms.ClienteForm(deserialize_form(customer_form), instance=updated_entity.id_cliente)
            if form.is_valid() and impuestos_form.is_valid() and info_adicional_form.is_valid() and customer_form.is_valid():
                cliente = customer_form.save()
                entity = form.save(id_cliente=cliente, commit=False)
                entity.save()
                impuestos_form.instance = entity
                impuestos_form.save()                
                info_adicional_form.instance = entity
                info_adicional_form.save()
                
                helper = helpers.IMPDComprobanteRetencionHelper(request, impuestos_form, info_adicional_form)
                helper.update(entity)
                save_all_helper = helpers.SaveAllHelper(dajax, 'retencion', 'retenciones', helper)
                dajax.script('bootbox.alert("DOCUMENTO ACTUALIZADO");')
                return save_all_helper.ajax_response()
            else:
                save_all_helper = helpers.SaveAllHelper(dajax, 'retencion', 'retenciones')
                return save_all_helper.manage_errors(form, None, customer_form, impuestos_form, info_adicional_form)
    except Exception as e:
        dajax.alert("update_retencion - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(update_retencion)

def generar_archivo_retencion(request, retencion_id):
    dajax = Dajax()
    try:
        helper = helpers.IMPDComprobanteRetencionHelper(request)
        retencion = helper.generar_archivo(retencion_id)
        dajax.script('bootbox.alert("RETENCION %s generada con exito. En unos minutos se procede a su AUTORIZACION");' % retencion.secuencial)
    except Exception as e:
        dajax.alert("Error al Generar archivo para RETENCION: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    dajax.script("window.location = '/imprenta-digital/retenciones/';");
    return dajax.json()

dajaxice_functions.register(generar_archivo_retencion)

def filter_impd_facturas(request, form):
    helper = helpers.FiltroFacturasAjaxHelper(request)
    return helper.process_filter(form)

dajaxice_functions.register(filter_impd_facturas)

def filter_impd_retenciones(request, form):
    helper = helpers.FiltroRetencionesAjaxHelper(request)
    return helper.process_filter(form)

dajaxice_functions.register(filter_impd_retenciones)

def filter_impd_guias(request, form):
    helper = helpers.FiltroGuiasAjaxHelper(request)
    return helper.process_filter(form)

dajaxice_functions.register(filter_impd_guias)

'''
---------------------------------
NOTA DE DEBITO
---------------------------------
'''

def save_nota_debito(request, form, config_form, customer_form):
    dajax = Dajax()
    try:
        des_form = deserialize_form(form)
        form = forms.NotaDebitoForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa})
        impuestos_form = forms.ImpdNDImpuestosFormSet(des_form)
        info_motivos_form = forms.ImpdNDMotivosFormSet(des_form)
        info_adicional_form = forms.ImpdNDInfoAdFormSet(des_form)
        config_form = forms.ConfiguracionFacturaForm(deserialize_form(config_form))
        customer_form = forms.ClienteForm(deserialize_form(customer_form))
        if (form.is_valid() and impuestos_form.is_valid() and info_motivos_form.is_valid() and
            info_adicional_form.is_valid() and config_form.is_valid() and customer_form.is_valid()):
            helper = helpers.IMPDNotaDebitoHelper(request, impuestos_form, info_motivos_form, info_adicional_form)
            save_all_helper = helpers.SaveAllHelper(dajax, 'notadebito', 'notasdebito', helper)
            dajax.script('bootbox.alert("DOCUMENTO GUARDADO");')
            return save_all_helper.saveAll(form, config_form, customer_form, impuestos_form, info_motivos_form, info_adicional_form)
        else:
            print 'ERRORES'
            print form.errors
            print impuestos_form.errors
            print info_motivos_form.errors
            print customer_form.errors
            print info_adicional_form.errors
            print config_form.errors
            save_all_helper = helpers.SaveAllHelper(dajax, 'notadebito', 'notasdebito')
            return save_all_helper.manage_errors(form, config_form, customer_form, impuestos_form, info_motivos_form, info_adicional_form)
    except Exception as e:
        dajax.alert("save_nota_debito - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(save_nota_debito)

def update_nota_debito(request, form, config_form, customer_form):
    dajax = Dajax()
    try:
        updated_entity = request.session['updated-entity']
        des_form = deserialize_form(form)
        if updated_entity:
            form = forms.NotaDebitoForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa}, instance=updated_entity)
            impuestos_form = forms.ImpdNDImpuestosFormSet(des_form, instance=updated_entity)
            info_motivos_form = forms.ImpdNDMotivosFormSet(des_form, instance=updated_entity)
            info_adicional_form = forms.ImpdNDInfoAdFormSet(des_form, instance=updated_entity)
            customer_form = forms.ClienteForm(deserialize_form(customer_form), instance=updated_entity.id_cliente)
            if form.is_valid() and impuestos_form.is_valid() and info_motivos_form.is_valid()\
                and info_adicional_form.is_valid() and customer_form.is_valid():
                cliente = customer_form.save()
                entity = form.save(id_cliente=cliente, commit=False)
                entity.save()
                impuestos_form.instance = entity
                impuestos_form.save()
                info_motivos_form.instance = entity
                info_motivos_form.save()
                info_adicional_form.instance = entity
                info_adicional_form.save()
                
                helper = helpers.IMPDNotaDebitoHelper(request, impuestos_form, info_motivos_form, info_adicional_form)
                helper.update(entity)
                save_all_helper = helpers.SaveAllHelper(dajax, 'notadebito', 'notasdebito', helper)
                dajax.script('bootbox.alert("DOCUMENTO ACTUALIZADO");')
                return save_all_helper.ajax_response()
            else:
                save_all_helper = helpers.SaveAllHelper(dajax, 'notadebito', 'notasdebito')
                return save_all_helper.manage_errors(form, None, customer_form, impuestos_form, info_motivos_form, info_adicional_form)
    except Exception as e:
        dajax.alert("update_nota_debito - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(update_nota_debito)

def generar_archivo_nota_debito(request, nota_debito_id):
    dajax = Dajax()
    try:
        helper = helpers.IMPDNotaDebitoHelper(request)
        nota_debito = helper.generar_archivo(nota_debito_id)
        dajax.script('bootbox.alert("NOTA DEBITO %s generada con exito. En unos minutos se procede a su AUTORIZACION");' % nota_debito.secuencial)
    except Exception as e:
        dajax.alert("Error al Generar archivo para NOTA DEBITO: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    dajax.script("window.location = '/imprenta-digital/notasdebito/';");
    return dajax.json()

dajaxice_functions.register(generar_archivo_nota_debito)

'''
----------------------------
NUEVO: NOTA DE CREDITO
----------------------------
'''

def filter_impd_notascredito(request, form):
    helper = helpers.FiltroNotasCreditoAjaxHelper(request)
    return helper.process_filter(form)

dajaxice_functions.register(filter_impd_notascredito)

def recalc_nota_credito(request, form, items):
    dajax = Dajax()
    try:
        total_sin_impuestos = 0
        total_impuestos = 0
        total_descuentos = 0
        for item in items:
            producto = models.ImpdProducto.objects.get(pk = item['producto'])
            total_descuentos += float(item['descuento'])
            subtotal = (float(item['cantidad']) * float(producto.precio_unitario)) - float(item['descuento'])
            dajax.assign(item['input_id']+'precio_unitario', 'value', str(producto.precio_unitario))
            dajax.assign(item['input_id']+'precio_total', 'value', str(subtotal))
            
            impuestos_producto = float(producto.get_impuestos(subtotal))
            total_impuestos += impuestos_producto
            total_sin_impuestos += float(subtotal)
            
        
        html = render_to_string('emisores/imprenta_digital/notacredito/totales-notacredito.html', {
            'total_descuentos': total_descuentos,
            'total_impuestos': total_impuestos,
            'total_sin_impuestos': total_sin_impuestos,
            'total':(total_sin_impuestos + total_impuestos)})
        dajax.assign('#widget-totales-notacredito', 'innerHTML', html)
        
        try:
            updated_entity = request.session['updated-entity']
        except:
            updated_entity = None
        
        des_form = deserialize_form(form)
        if updated_entity:
            form = forms.NotaCreditoForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa}, instance=updated_entity)
            item_notacredito_form = forms.ItemNotaCreditoFormSet(request.user.get_profile().ruc_empresa, des_form, instance=updated_entity)
        else:
            form = forms.NotaCreditoForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa})
            item_notacredito_form = forms.ItemNotaCreditoFormSet(request.user.get_profile().ruc_empresa, des_form)
        form.is_valid()
        item_notacredito_form.is_valid()
        print 'OK'
    except Exception as e:
        print "recalc_nota_credito - Error: %s" % str(e)
        traceback.print_exc()
    dajax.script('hideSmallWait();')
    return dajax.json()

dajaxice_functions.register(recalc_nota_credito)

def save_nota_credito(request, form, config_form, customer_form):
    dajax = Dajax()
    try:
        des_form = deserialize_form(form)
        form = forms.NotaCreditoForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa})
        item_notacredito_form = forms.ItemNotaCreditoFormSet(request.user.get_profile().ruc_empresa, des_form)
        info_adicional_form = forms.InformacionAdicionalNotaCreditoFormSet(des_form)
        config_form = forms.ConfiguracionFacturaForm(deserialize_form(config_form))
        customer_form = forms.ClienteForm(deserialize_form(customer_form))
        if (form.is_valid() and item_notacredito_form.is_valid() and info_adicional_form.is_valid() and
            config_form.is_valid() and customer_form.is_valid()):
            helper = helpers.IMPDNotaCreditoHelper(request, item_notacredito_form, form, info_adicional_form)
            save_all_helper = helpers.SaveAllHelper(dajax, 'notacredito', 'notascredito', helper)
            dajax.script('bootbox.alert("DOCUMENTO GUARDADO");')
            return save_all_helper.saveAll(form, config_form, customer_form, item_notacredito_form, info_adicional_form)
        else:
            save_all_helper = helpers.SaveAllHelper(dajax, 'notacredito', 'notascredito')
            return save_all_helper.manage_errors(form, config_form, customer_form, item_notacredito_form, info_adicional_form)
    except Exception as e:
        dajax.alert("save_nota_credito - Error: %s" % str(e))
        traceback.print_exc()
    return dajax.json()

dajaxice_functions.register(save_nota_credito)

def update_nota_credito(request, form, config_form, customer_form):
    dajax = Dajax()
    try:
        updated_entity = request.session['updated-entity']
        des_form = deserialize_form(form)
        if updated_entity:            
            form = forms.NotaCreditoForm(des_form, initial={'ruc_empresa': request.user.get_profile().ruc_empresa}, instance=updated_entity)
            item_notacredito_form = forms.ItemNotaCreditoFormSet(request.user.get_profile().ruc_empresa, des_form, instance=updated_entity)
            info_adicional_form = forms.InformacionAdicionalNotaCreditoFormSet(des_form, instance=updated_entity)
            customer_form = forms.ClienteForm(deserialize_form(customer_form), instance=updated_entity.id_cliente)
            if form.is_valid() and item_notacredito_form.is_valid()\
                and info_adicional_form.is_valid() and customer_form.is_valid():
                cliente = customer_form.save()
                entity = form.save(id_cliente=cliente, commit=False)
                entity.save()
                item_notacredito_form.instance = entity
                item_notacredito_form.save()
                info_adicional_form.instance = entity
                info_adicional_form.save()
                
                helper = helpers.IMPDNotaCreditoHelper(request, item_notacredito_form, form, info_adicional_form)
                helper.update(entity)
                save_all_helper = helpers.SaveAllHelper(dajax, 'notacredito', 'notascredito', helper)
                dajax.script('bootbox.alert("DOCUMENTO ACTUALIZADO");')
                return save_all_helper.ajax_response()
            else:
                save_all_helper = helpers.SaveAllHelper(dajax, 'notacredito', 'notascredito')
                return save_all_helper.manage_errors(form, None, customer_form, item_notacredito_form, info_adicional_form)
    except Exception as e:
        dajax.alert("update_nota_credito - Error: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(update_nota_credito)

def generar_archivo_nota_credito(request, nota_credito_id):
    dajax = Dajax()
    try:
        helper = helpers.IMPDNotaCreditoHelper(request)
        nota_credito = helper.generar_archivo(nota_credito_id)
        dajax.script('bootbox.alert("NOTA CREDITO %s generada con exito. En unos minutos se procede a su AUTORIZACION");' % nota_credito.secuencial)
    except Exception as e:
        dajax.alert("Error al Generar archivo para NOTA CREDITO: %s" % str(e))
        traceback.print_exc()
    dajax.script('hideWait();')
    dajax.script("window.location = '/imprenta-digital/notascredito/';");
    return dajax.json()

dajaxice_functions.register(generar_archivo_nota_credito)

'''
----------------------------
NUEVO-FIN: NOTA DE CREDITO
----------------------------
'''
def recalc_row(dajax, product_id, id_input, quantity, discount):
    try:
        producto = models.ImpdProducto.objects.get(pk = product_id)
        if quantity is None or quantity == '': quantity = 0
        if discount is None or discount == '': discount = 0
        total = float(quantity) * (float(producto.precio_unitario) - float(discount))
        impuestos_producto = float(producto.get_impuestos(subtotal))
        dajax.assign(id_input+'precio_unitario', 'value', str(producto.precio_unitario))
        dajax.assign(id_input+'precio_total', 'value', str(total + impuestos_producto))
    except Exception as e:
        print 'Error al recalcular', e

def display_product_data(request, product_id, id_input):
    dajax = Dajax()
    try:
        producto = models.ImpdProducto.objects.get(pk = product_id)
        dajax.assign(id_input+'precio_unitario', 'value', str(producto.precio_unitario))
    except Exception as e:
        print 'Error al recalcular', e
    return dajax.json()

dajaxice_functions.register(display_product_data)

def bind_product_form(request, product_id, nombre_registro, initial_description):
    dajax = Dajax()
    try:
        if product_id:
            producto = models.ImpdProducto.objects.get(pk = product_id)
        else:
            producto = models.ImpdProducto()
        
        if initial_description and not product_id:
            producto_form = forms.ProductoForm(instance = producto, initial={'descripcion':initial_description})
        else:
            producto_form = forms.ProductoForm(instance = producto)
        
        detalle_adicional_producto_form = forms.ProductoDetalleAdicionalFormSet(instance = producto)
        impuestos_producto_form = forms.ProductoImpuestoFormSet(instance = producto)
        
        html = render_to_string('emisores/imprenta_digital/producto.html', {'producto_form': producto_form,
                                                                            'detalle_adicional_producto_form': detalle_adicional_producto_form,
                                                                            'impuestos_producto_form': impuestos_producto_form})
        dajax.assign('#contenido-producto', 'innerHTML', html)
        dajax.script('jQuery.noConflict();')
        dajax.script('$("#buton-crear-prod").click();')
        dajax.assign('#id_id_registro', 'value', str(product_id))
        dajax.assign('#id_nombre_registro', 'value', str(nombre_registro))
    except Exception as e:
        print 'Error al cargar producto', e
    dajax.script('hideSmallWait();')
    return dajax.json()

dajaxice_functions.register(bind_product_form)

def bind_destinatario_form(request, destinatario_id):
    dajax = Dajax()
    try:
        if destinatario_id:
            destinatario = models.ImpdGRDestinatario.objects.get(pk = destinatario_id)
        else:
            destinatario = models.ImpdGRDestinatario()
        
        destinatario_form = forms.ImpdDestinatarioForm(instance = destinatario)        
        html = render_to_string('emisores/imprenta_digital/guiaremision/destinatario.html', {'destinatario_form': destinatario_form})
        dajax.assign('#contenido-destinatario', 'innerHTML', html)
        dajax.script('jQuery.noConflict();')
        dajax.script('$("#buton-crear-dest").click();')
        dajax.assign('#id_id_registro_destinatario', 'value', str(destinatario_id))
    except Exception as e:
        print 'Error al cargar destinatario', e
    dajax.script('hideSmallWait();')
    return dajax.json()

dajaxice_functions.register(bind_destinatario_form)

def filter_impd_notasdebito(request, form):
    helper = helpers.FiltroNotasDebitoAjaxHelper(request)
    return helper.process_filter(form)

dajaxice_functions.register(filter_impd_notasdebito)

def add_special_ruc(request, ruc):
    dajax = Dajax()
    if ruc:
        if len(ruc) == 13:
            if ruc.isdigit():
                if doc_validator.add_special_ruc(ruc, request.user):
                    dajax.script('bootbox.alert("Se ha registrado el RUC especial %s.");' % ruc)
                else:
                    dajax.script('bootbox.alert("Aquel RUC especial ya fue agregado anteriormente.");')
            else:
                dajax.script('bootbox.alert("Todo RUC debe ser numerico.");')
        else:
            dajax.script('bootbox.alert("Todo RUC debe tener 13 caracteres.");')
    else:
        dajax.script('bootbox.alert("Es necesario un RUC para agregar a listado especial.");')
    dajax.script('hideSmallWait();')
    return dajax.json()

dajaxice_functions.register(add_special_ruc)

def get_impuestos_reembolso(request, item_prefix):
    dajax = Dajax()
    try:
        impuestos_reembolsos = request.session['impuestos-reembolso-'+item_prefix]
        data = transform_imp_rem_list_to_dict(impuestos_reembolsos)
        if data:
            formset = forms.ImpdImpuestoReembolsoFormSet(data)
        else:
            formset = forms.ImpdImpuestoReembolsoFormSet()
        html = render_to_string('emisores/imprenta_digital/factura/impuestos-reembolso.html',
                                {'impuestos_reembolsos_formset': formset})
    except Exception as e:
        print 'get_impuestos_reembolso - ERROR', e
        html = render_to_string('emisores/imprenta_digital/factura/impuestos-reembolso.html',
                                {'impuestos_reembolsos_formset': forms.ImpdImpuestoReembolsoFormSet()})

    request.session['current-reembolso'] = item_prefix
    dajax.assign('#impuestos-reembolso', 'innerHTML', html)
    dajax.script('hideWait();')
    dajax.script('openImpReembolsoModal();')
    return dajax.json()

dajaxice_functions.register(get_impuestos_reembolso)

def add_impuestos_reembolso(request, form_impuestos_reembolso):
    dajax = Dajax()

    try:
        item_prefix = request.session['current-reembolso']
        print 'GUARDANDO IMP PARA REEMBOLSO', item_prefix
        des_form = deserialize_form(form_impuestos_reembolso)
        formset = forms.ImpdImpuestoReembolsoFormSet(des_form)

        data = []

        errors = False
        for form in formset:
            print '--> FORM', form
            if form.is_valid():
                data.append(form.get_dict())
            else:
                print form.errors
                errors = True

        request.session['impuestos-reembolso-'+item_prefix] = data
        if errors:
            dajax.alert('Existen errores en los campos de impuestos del reembolso')
        else:
            dajax.script('closeImpReembolsoModal();')

    except Exception as e:
        dajax.alert("add_impuestos_reembolso - Error: %s" % str(e))
        traceback.print_exc()

    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(add_impuestos_reembolso)

def transform_imp_rem_list_to_dict(items_list):
    data = None

    if len(items_list) > 0:
        data = {
            'form-TOTAL_FORMS': '%d' % len(items_list),
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '10',
        }

        counter = 0
        for item in items_list:
            print '--> ITEM', item
            data['form-%d-codigo_reembolso' % counter] = item['codigo_reembolso']
            data['form-%d-codigo_porcentaje_rembolso' % counter] = item['codigo_porcentaje_rembolso']
            data['form-%d-tarifa_reembolso' % counter] = item['tarifa_reembolso']
            data['form-%d-base_imponible_reembolso' % counter] = item['base_imponible_reembolso']
            data['form-%d-impuesto_reembolso' % counter] = item['impuesto_reembolso']
            counter += 1

    return data
