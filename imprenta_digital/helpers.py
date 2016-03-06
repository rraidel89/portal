# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.core.cache import cache
from django.conf import settings

from core import mixins, tasks
from django.db.models.query_utils import Q
from innobee_portal import properties as P

from django.db import IntegrityError, transaction
from django.db.models import Max, Sum

from django.contrib import messages
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from django.template.context import RequestContext, Context
from xml.etree import ElementTree as ET

from core.helper import FiltroHelper, FiltroAjaxHelper

from dajax.core import Dajax
from dajaxice.utils import deserialize_form

import traceback
import models
import datetime
import generators

CACHE_EXPIRATION_CATALOGS = 360 #6 horas de cache

class IMPDCatalogoHelper(object):
    
    def get_catalogo(self, modulo, to_decimal=False):
        key = 'impd-cat-%s' % modulo
        catalogos = cache.get(key)
        if catalogos is None:
            from core import models
            catalogos =  []
            catalogos_query = models.ImpdCatalogo.objects.filter(modulo = modulo, estado=mixins.get_active_status()).order_by('descripcion')
            try:
                if catalogos_query.count() > 0:
                    for c in catalogos_query:
                        if to_decimal:
                            catalogos.append( ( int(self.get_valor(c)), c.descripcion) )
                            
                        else:
                            catalogos.append( ( self.get_valor(c), c.descripcion) )
            except Exception as e:
                print e
            
            if catalogos and len(catalogos)>0:
                cache.set(key, catalogos, 60*CACHE_EXPIRATION_CATALOGS)
        return catalogos
    
    def get_catalogos_dependientes(self, catalog_module, catalog_value, source_module, to_decimal=False):
        key = 'impd-dep-cat-%s-%s-%s' % (catalog_module,catalog_value, source_module)
        print 'get_catalogos_dependientes - Key Search', key
        catalogos = cache.get(key)
        if catalogos is None:
            from core import models
            catalogos =  []
            if not source_module:
                catalogos_query = models.ImpdCatalogo.objects.filter(modulo_dependencia = catalog_module, valor_dependencia = catalog_value).order_by('descripcion')
            else:
                catalogos_query = models.ImpdCatalogo.objects.filter(modulo=source_module, modulo_dependencia = catalog_module, valor_dependencia = catalog_value).order_by('descripcion')
            
            if catalogos_query.count() > 0:
                for c in catalogos_query:
                    if to_decimal:
                        catalogos.append( {'value': str(int(self.get_valor(c))), 'label': c.descripcion })
                    else:
                        catalogos.append( {'value': str(self.get_valor(c)), 'label': c.descripcion })
                print 'get_catalogos_dependientes - DEPENDENCIA CATALOGOS', catalogos, '\nkey:', key
                cache.set(key, catalogos, 60*CACHE_EXPIRATION_CATALOGS)
            else:
                print 'get_catalogos_dependientes - NO ENCONTRADOS'
        return catalogos

    def get_valor(self, c):
        if c.tipo == P.TIPO_TEXTO:
            return c.valor.strip()
        elif c.tipo == P.TIPO_NUMERO:
            return float(c.valor.strip())
        elif c.tipo == P.TIPO_BOOLEAN:
            return bool(c.valor.strip())

catalogo_helper = IMPDCatalogoHelper()

class IMPDSecuencialHelper(object):
    
    def get_next_secuencial(self, secuenciales_entity, configuracion):
        try:
            if len(secuenciales_entity) > 0 and secuenciales_entity[0]['max_secuencial'] > 0:
                secuencial = secuenciales_entity[0]
                max_secuencial = secuencial['max_secuencial']
                max_secuencial = int(max_secuencial) + 1
                if max_secuencial <= 999999999:
                    secuencial = str(max_secuencial).zfill(9)
                else:
                    secuencial = configuracion.secuencial_inicial.zfill(9)
            else:
                secuencial = configuracion.secuencial_inicial
                
            print 'SECUENCIAL', secuencial
        except Exception as e:
            print 'get_next_secuencial - Error', e
            secuencial = configuracion.secuencial_inicial.zfill(9)
            print 'SECUENCIAL EX', secuencial
        return secuencial
    
    def get_next_secuencial_factura_intern(self, configuracion):
        import models
        secuenciales_facturas = models.ImpdFactura.objects.filter(id_configuracion = configuracion)\
                                            .values('secuencial_number').annotate(max_secuencial=Max('secuencial_number')).order_by('-secuencial_number')
        return self.get_next_secuencial(secuenciales_facturas, configuracion)
    
    def get_next_secuencial_guia_remision_intern(self, configuracion):
        import models
        secuenciales = models.ImpdGuiaRemision.objects.filter(id_configuracion = configuracion)\
                                            .values('secuencial_number').annotate(max_secuencial=Max('secuencial_number')).order_by('-secuencial_number')
        return self.get_next_secuencial(secuenciales, configuracion)
    
    def get_next_secuencial_retencion_intern(self, configuracion):
        import models
        secuenciales = models.ImpdComproRetencion.objects.filter(id_configuracion = configuracion)\
                                            .values('secuencial_number').annotate(max_secuencial=Max('secuencial_number')).order_by('-secuencial_number')
        return self.get_next_secuencial(secuenciales, configuracion)
    
    def get_next_secuencial_nota_debito_intern(self, configuracion):
        import models
        secuenciales = models.ImpdNotaDebito.objects.filter(id_configuracion = configuracion)\
                                            .values('secuencial_number').annotate(max_secuencial=Max('secuencial_number')).order_by('-secuencial_number')
        return self.get_next_secuencial(secuenciales, configuracion)
    
    def get_next_secuencial_notacredito_intern(self, configuracion):
        import models
        secuenciales_notas_credito = models.ImpdNotaCredito.objects.filter(id_configuracion = configuracion)\
                                            .values('secuencial_number').annotate(max_secuencial=Max('secuencial_number')).order_by('-secuencial_number')
        return self.get_next_secuencial(secuenciales_notas_credito, configuracion)
    
    def get_next_secuencial_factura(self, factura):
        return self.get_next_secuencial_factura_intern(factura.id_configuracion)
    
    def get_next_secuencial_guia_remision(self, guia):
        return self.get_next_secuencial_guia_remision_intern(guia.id_configuracion)
        
    def get_next_secuencial_retencion(self, retencion):
        return self.get_next_secuencial_retencion_intern(retencion.id_configuracion)
        
    def get_next_secuencial_nota_debito(self, notadebito):
        return self.get_next_secuencial_nota_debito_intern(notadebito.id_configuracion)
        
    def get_next_secuencial_notacredito(self, notacredito):
        return self.get_next_secuencial_notacredito_intern(notacredito.id_configuracion)
        
secuencial_helper = IMPDSecuencialHelper()

class ComprobanteHelper(object):
    
    def get_file_name(self, entity):
        ahora = datetime.datetime.now()
        file_name = '%s%s%s%s%s%s%s%s%s.XML' % (
                    self.tipo,
                    str(entity.ruc_empresa),
                    entity.id_configuracion.establecimiento,
                    entity.id_configuracion.punto_emision,
                    entity.secuencial,
                    ahora.strftime("%d%m%Y"), str(ahora.hour).zfill(2), str(ahora.minute).zfill(2),
                    str(ahora.second).zfill(2))
        return file_name

    def upload_file(self, entity, xml_data, temporal_file_path):
        tree = ET.XML(xml_data.encode('utf8'))
        print 'generar_archivo - Subiendo el Archivo', temporal_file_path
        with open(temporal_file_path, "w") as f:
            f.write(ET.tostring(tree))
        tasks.subir_SFTP(entity.ruc_empresa, temporal_file_path)
        print 'generar_archivo - Archivo', temporal_file_path, 'enviado al SFTP, esperando respuesta...'
    
    def get_template_by_type(self):
        tipo = self.tipo
        if tipo == 'FT':
            return 'factura'
        elif tipo == 'GR':
            return 'guiaremision'
        elif tipo == 'CR':
            return 'comproretencion'
        elif tipo == 'ND':
            return 'notadebito'
        elif tipo == 'NC':
            return 'notacredito'

    def convertir_pdf(self, entity):
        template_name = self.get_template_by_type()
        processor = generators.PDFGenerator('comprobantes/preview/%s-template.html' % template_name,
                                            entities={'entity': entity})
        return processor.process(self.request)
    
    def preview(self, entity):
        template_name = self.get_template_by_type()
        entity_template_path = 'comprobantes/preview/%s-template.html' % template_name
        return render_to_response('comprobantes/preview/comprobante.html',
                    {'entity':entity, 'tipo':self.tipo}, context_instance=RequestContext(self.request))

def calc_item_total(row):
    if row.cantidad is None: row.cantidad = 0
    if row.descuento is None: row.descuento = 0
    return float(row.cantidad) * float(row.id_producto.precio_unitario) - float(row.descuento)

from wkhtmltopdf.views import PDFTemplateResponse

class IMPDFacturaHelper(ComprobanteHelper):
    
    def __init__(self, request=None, formset=None, form=None, formset_adicional=None, reembolso_factura=None, pago_factura=None):
        self.formset = formset
        self.request = request
        if request:
            self.user = request.user
        else:
            self.user = None
        if form:
            try:
                self.propina = form.get_propina()
            except:
                self.propina = 0
        else:
            self.propina = None
        self.formset_adicional = formset_adicional
        self.tipo = 'FT'
        self.reembolso_factura = reembolso_factura
        self.pago_factura = pago_factura
    
    def calc_totals(self):
        try:
            print 'IMPDFacturaHelper - Calculando Factura Formset'
            instances = self.formset.save(commit=False)
            factura = None
            total_sin_impuestos = 0
            total_con_impuestos = 0
            total_descuentos = 0
            total_impuestos = 0
            print 'INSTANCES', instances
            for instance in instances:
                print '--> INSTANCE CALC', instance
                if isinstance(instance, models.ImpdItemFactura):
                    print '--> ITEM', instance
                    '''
                    El subtotal es la cantidad por el precio unitario configurado del producto y la resta del descuento,
                    por lo general descuento es 0 asi que la resta es el mismo subtotal
                    '''
                    item_subtotal = calc_item_total(instance)
                    total_descuentos += float(instance.descuento)
                    
                    print '--> TOTAL', item_subtotal
                    
                    '''
                    Se calculan los impuestos del item en base a los impuestos configurados
                    del producto y el subtotal calculado (item_subtotal)
                    '''
                    for prod_imp in instance.id_producto.impdproductoimpuesto_set.all():
                        valor = float(prod_imp.tarifa) * 0.01 * float(item_subtotal)
                        
                        impuestos_factura_producto = instance.impditemfacturaimpuesto_set.all().filter(
                            producto_impuesto = prod_imp)
                        if impuestos_factura_producto.count() == 0:
                            impuesto_item_factura = models.ImpdItemFacturaImpuesto()
                            impuesto_item_factura.item_factura = instance
                            impuesto_item_factura.producto_impuesto = prod_imp
                            impuesto_item_factura.base_imponible = item_subtotal
                            impuesto_item_factura.valor = float(prod_imp.tarifa) * 0.01 * float(item_subtotal)
                            impuesto_item_factura.save(user = self.user)
                        else:
                            ifp = impuestos_factura_producto[0]
                            ifp.producto_impuesto = prod_imp
                            ifp.base_imponible = item_subtotal
                            ifp.valor = float(prod_imp.tarifa) * 0.01 * float(item_subtotal)
                            ifp.save(user = self.user)
                    
                    impuestos_producto = float(instance.id_producto.get_impuestos(item_subtotal))
                    print 'Impuestos', impuestos_producto
                    
                    total_impuestos += impuestos_producto
                    total_sin_impuestos += item_subtotal
                    total_con_impuestos +=  float(item_subtotal) + float(impuestos_producto)
                    
                    instance.total_sin_impuestos = item_subtotal
                    instance.save()
                    
            total = total_con_impuestos + float(self.propina)
        except Exception as e:
            traceback.print_exc()
            raise e
        
        return total_sin_impuestos, total_con_impuestos, total_descuentos, total_impuestos
    
    def save_detalles_adicionales(self):
        self.formset_adicional.save()

    def save_reembolsos(self):
        if self.reembolso_factura:
            self.reembolso_factura.save()
            self.save_imp_reem(self.reembolso_factura)

        if self.pago_factura:
            self.pago_factura.save()

    def save_imp_reem(self, formset):
        counter = 0
        print 'INSTANCES REEM', formset
        for form in formset:
            instance = form.instance
            print '--> INSTANCIA REEM', instance, 'ID', instance.pk
            try:
                impuestos = self.request.session['impuestos-reembolso-%d' % counter]

                last_items = models.ImpdFactDetalleImpuestoReembolso.objects.filter(reembolso = instance)
                for last_item in last_items:
                    last_item.delete()

                for item in impuestos:
                    print 'GUARDANDO', item
                    imp_reem = models.ImpdFactDetalleImpuestoReembolso()
                    imp_reem.codigo_reembolso = item['codigo_reembolso']
                    imp_reem.codigo_porcentaje_rembolso= item['codigo_porcentaje_rembolso']
                    imp_reem.tarifa_reembolso = item['tarifa_reembolso']
                    imp_reem.base_imponible_reembolso = item['base_imponible_reembolso']
                    imp_reem.impuesto_reembolso = item['impuesto_reembolso']
                    imp_reem.reembolso = instance
                    imp_reem.save()
                    print 'GUARDADO!'

                del self.request.session['impuestos-reembolso-%d' % counter]
            except Exception as e:
                print 'save_reembolsos - ERROR', e
            counter += 1
        
    def update(self, entity):
        total_sin_impuestos, total_con_impuestos, total_descuentos, total_impuestos = self.calc_totals()
        if total_con_impuestos > 0:
            entity.total_sin_impuestos = total_sin_impuestos
            entity.total = total_con_impuestos
            entity.descuento = total_descuentos
            entity.impuestos = total_impuestos
            entity.save()
        
    def save(self, entity):
        instances = self.formset.save(commit=False)
        factura = None
        subtotal = 0
        total_con_impuestos = 0
        total_descuentos = 0
        total_impuestos = 0
        for instance in instances:
            print '--> INSTANCE SAVING', instance
            if isinstance(instance, models.ImpdItemFactura):
                '''
                El subtotal es la cantidad por el precio unitario configurado del producto y la resta del descuento,
                por lo general descuento es 0 asi que la resta es el mismo subtotal
                '''
                item_subtotal = calc_item_total(instance)
                total_descuentos += float(instance.descuento)       
                impuestos_item = 0
                instance.save()
                                 
                '''
                Se calculan los impuestos del item en base a los impuestos configurados
                del producto y el subtotal calculado (item_subtotal)
                '''
                for prod_imp in instance.id_producto.impdproductoimpuesto_set.all():
                    impuesto_item_factura = models.ImpdItemFacturaImpuesto()
                    impuesto_item_factura.item_factura = instance
                    impuesto_item_factura.producto_impuesto = prod_imp
                    impuesto_item_factura.base_imponible = item_subtotal
                    impuesto_item_factura.valor = float(prod_imp.tarifa) * 0.01 * float(item_subtotal)
                    impuesto_item_factura.save(user = self.user)
                    impuestos_item += impuesto_item_factura.valor

                instance.total_sin_impuestos = item_subtotal
                instance.save(user = self.user)
                
                total_impuestos += impuestos_item
                subtotal += instance.total_sin_impuestos
                total_con_impuestos +=  float(item_subtotal) + float(impuestos_item)
            else:
                instance.save(user = self.user)
        
        if entity:
            entity.total_sin_impuestos = subtotal
            entity.descuento = total_descuentos
            entity.impuestos = total_impuestos
            entity.total = total_con_impuestos + float(entity.propina)
            entity.save(user = self.user)
        
        print '--> GUARDANDO 4'
        self.formset.save_m2m()
        self.save_detalles_adicionales()
        self.save_reembolsos()
    
    def generar_archivo(self, id):
        factura = None
        try:
            factura = models.ImpdFactura.objects.get(pk=id)
            xml_data = render_to_string('comprobantes/factura.html', {'entity': factura})
            ruta = tasks.get_directorio_entrada(factura.ruc_empresa)
            if ruta:
                file_name = self.get_file_name(factura)
                factura.codigo_original = file_name.replace('.XML','')
                factura.save()
                temporal_file_path = "media/imprenta-digital/facturas/%s" % file_name
                self.upload_file(factura, xml_data, temporal_file_path)
                messages.success(self.request,
                                 'Factura %s creada y enviada con exito al directorio de tipo %s, el proceso tomara un par de minutos.' % (
                                     factura.codigo_original, P.DIRECTORIO_ENTRADA))
            else:
                messages.error(self.request,
                               'La empresa seleccionada no tiene definido un directorio de tipo ' + P.DIRECTORIO_ENTRADA)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al procesar la factura: %s' % str(e1))
        return factura
    
    def ver_xml(self, id):
        try:
            return self.preview(models.ImpdFactura.objects.get(pk=id))
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al previsualizar comprobante: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/facturas/')

    def to_pdf(self, id):
        try:
            return self.convertir_pdf(models.ImpdFactura.objects.get(pk=id))
        except Exception as e:
            messages.error(self.request, 'Error al generar pdf del comprobante: %s' % str(e))
        return HttpResponseRedirect('/imprenta-digital/facturas/')

    def desactivar(self, id):
        entity = None
        try:
            entity = models.ImpdFactura.objects.get(pk=id)
            entity.estado = mixins.get_inactive_status()
            entity.save()
            messages.success(self.request, 'Factura %s deshabilitada.' % entity.secuencial)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al desactivar la factura: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/facturas/')

class IMPDGuiaRemisionHelper(ComprobanteHelper):
    
    def __init__(self, request, detalle_destinatario_form=None, productos_detalle_destinatario=None, aditional_formset=None):
        self.detalle_destinatario_form = detalle_destinatario_form
        self.productos_detalle_destinatario = productos_detalle_destinatario
        self.request = request
        self.user = request.user
        self.aditional_formset = aditional_formset
        self.tipo = 'GR'
    
    def save(self, entity):
        detalle_destinatario = self.detalle_destinatario_form.save(entity)
        self.productos_detalle_destinatario.instance = detalle_destinatario
        self.productos_detalle_destinatario.save()
        self.aditional_formset.save()
    
    def update(self, entity):
        pass
    
    def generar_archivo(self, id):
        guia = None
        try:
            guia = models.ImpdGuiaRemision.objects.get(pk=id)
            xml_data = render_to_string('comprobantes/guiaremision.html', {'entity': guia})
            ruta = tasks.get_directorio_entrada(guia.ruc_empresa)
            if ruta:
                file_name = self.get_file_name(guia)
                guia.codigo_original = file_name.replace('.XML','')
                guia.save()
                temporal_file_path = "media/imprenta-digital/guiasremision/%s" % file_name
                self.upload_file(guia, xml_data, temporal_file_path)
                messages.success(self.request,
                                 'Guia de Remision %s creada y enviada con exito al directorio de tipo %s, el proceso tomara un par de minutos.' % (
                                     guia.codigo_original, P.DIRECTORIO_ENTRADA))
            else:
                messages.error(self.request,
                               'La empresa seleccionada no tiene definido un directorio de tipo ' + P.DIRECTORIO_ENTRADA)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al procesar la guia de remision: %s' % str(e1))
        return guia
    
    def ver_xml(self, id):
        try:
            return self.preview(models.ImpdGuiaRemision.objects.get(pk=id))
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al previsualizar comprobante: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/guiasremision/')

    def to_pdf(self, id):
        try:
            return self.convertir_pdf(models.ImpdGuiaRemision.objects.get(pk=id))
        except Exception as e:
            messages.error(self.request, 'Error al generar pdf del comprobante: %s' % str(e))
        return HttpResponseRedirect('/imprenta-digital/guiasremision/')
    
    def desactivar(self, id):
        entity = None
        try:
            entity = models.ImpdGuiaRemision.objects.get(pk=id)
            entity.estado = mixins.get_inactive_status()
            entity.save()
            messages.success(self.request, 'Guia de Remision %s deshabilitada.' % entity.secuencial)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al desactivar la guia de remision: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/guiasremision/')

class IMPDComprobanteRetencionHelper(ComprobanteHelper):
    
    def __init__(self, request, formset=None, aditional_formset=None):
        self.request = request
        self.user = request.user
        self.formset = formset
        self.aditional_formset = aditional_formset
        self.tipo = 'CR'
        
    def save(self, entity):
        self.formset.save()
        self.aditional_formset.save()
        
    def update(self, entity):
        pass
    
    def generar_archivo(self, id):
        retencion = None
        try:
            retencion = models.ImpdComproRetencion.objects.get(pk=id)
            xml_data = render_to_string('comprobantes/comproretencion.html', {'entity': retencion})
            ruta = tasks.get_directorio_entrada(retencion.ruc_empresa)
            if ruta:
                file_name = self.get_file_name(retencion)
                retencion.codigo_original = file_name.replace('.XML','')
                retencion.save()
                temporal_file_path = "media/imprenta-digital/retenciones/%s" % file_name
                self.upload_file(retencion, xml_data, temporal_file_path)
                messages.success(self.request,
                                 'Retencion %s creada y enviada con exito al directorio de tipo %s, el proceso tomara un par de minutos.' % (
                                     retencion.codigo_original, P.DIRECTORIO_ENTRADA))
            else:
                messages.error(self.request,
                               'La empresa seleccionada no tiene definido un directorio de tipo ' + P.DIRECTORIO_ENTRADA)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al procesar la guia de remision: %s' % str(e1))
        return retencion
    
    def ver_xml(self, id):
        try:
            return self.preview(models.ImpdComproRetencion.objects.get(pk=id))
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al previsualizar comprobante: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/retenciones/')

    def to_pdf(self, id):
        try:
            return self.convertir_pdf(models.ImpdComproRetencion.objects.get(pk=id))
        except Exception as e:
            messages.error(self.request, 'Error al generar pdf del comprobante: %s' % str(e))
        return HttpResponseRedirect('/imprenta-digital/facturas/')

    def desactivar(self, id):
        entity = None
        try:
            entity = models.ImpdComproRetencion.objects.get(pk=id)
            entity.estado = mixins.get_inactive_status()
            entity.save()
            messages.success(self.request, 'Retencion %s deshabilitada.' % entity.secuencial)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al desactivar la retencion: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/retenciones/')

class FiltroComprobantesHelper(FiltroHelper):
    
    def __init__(self):
        self.cleaned_data = None
    
    def get_common_query(self, queries, start_date, end_date, filas_docs):
        queries += [(Q(estado=mixins.get_active_status()) | Q(estado=mixins.get_anulado_status()))]
        if self.form and self.form.cleaned_data:
            self.cleaned_data = self.form.cleaned_data.copy()
            if self.cleaned_data:
                self.get_dates_query(queries, start_date, end_date)
                self.filas = self.cleaned_data[filas_docs]
        return queries
    
    def get_query_docs(self):
        queries = [Q(ruc_empresa=self.get_identificacion_usuario())]
        try:
            self.get_common_query(queries, 'fecha_desde', 'fecha_hasta', 'filas')
            if self.cleaned_data:
                if self.cleaned_data['secuencial']: queries += [Q(secuencial=self.cleaned_data['secuencial'])]
                if self.cleaned_data['identificacion_cliente']:
                    if self.tipo == 1 or self.tipo == 3:
                        queries += [Q(id_cliente__identificacion=self.cleaned_data['identificacion_cliente'])]
                if self.cleaned_data['razon_social_cliente']:
                    if self.tipo == 1 or self.tipo == 3:
                        queries += [Q(id_cliente__razon_social__icontains=self.cleaned_data['razon_social_cliente'])]
            print 'QUERIES', queries
        except Exception as e:
            print 'get_query_docs - Error:', e
        return self.build_query(queries)

    def get_identificacion(self):
        try:
            cleaned_data = self.form.cleaned_data.copy()
            return cleaned_data['identificacion_cliente']
        except:
            return None

    def get_razon_social(self):
        try:
            cleaned_data = self.form.cleaned_data.copy()
            return cleaned_data['razon_social_cliente']
        except:
            return None
    
    def process(self):
        query = self.get_query_docs()        
        documentos = []
        if query:
            documentos = self.get_documents(query)           
            self.request.session[self.session_name] = documentos
            self.cantidad = documentos.count()            
        return self.paginar(documentos)

class FiltroFacturasHelper(FiltroComprobantesHelper):

    def __init__(self, request, form):
        self.request = request
        self.form = form
        self.filas = 5
        self.suma_documentos = 0
        self.cantidad = 0
        self.page_name, self.session_name = self.get_names()
        self.tipo = 1
        
    def get_names(self):
        return 'page_impd_fact', 'impd-facturas'
    
    def get_documents(self, query):
        docs = models.ImpdFactura.objects.filter(query).order_by('-fecha_creacion')
        print 'Facturas encontradas:', docs.count()
        self.suma_documentos = docs.aggregate(Sum('total'))
        self.suma_documentos = self.suma_documentos['total__sum']
        return docs    

class FiltroFacturasAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
        
    def process_filter(self, form):
        import forms
        try:           
            form = forms.ConsultaFacturasForm(deserialize_form(form))
            if form.is_valid():
                helper = FiltroFacturasHelper(self.request, form)
                documentos = helper.process()
                if documentos:
                    html = render_to_string('emisores/imprenta_digital/factura/items-lista-factura.html', {'object_list': documentos})
                    self.dajax.assign('#facturas', 'innerHTML', html)
                    self.dajax.assign('#suma', 'innerHTML', str(helper.suma_documentos))
                else:
                    self.dajax.assign('#facturas', 'innerHTML', '')
                    self.dajax.assign('#suma', 'innerHTML', '0')
                    self.dajax.alert('No se encontraron datos con esos terminos de consulta')
            else:
                print form.errors
                self.dajax.alert('Por favor ingrese terminos de consulta correctos')
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))
        
        return self.return_ajax(self.dajax)

class FiltroGuiasHelper(FiltroComprobantesHelper):

    def __init__(self, request, form):
        self.request = request
        self.form = form
        self.filas = 5
        self.suma_documentos = 0
        self.cantidad = 0
        self.page_name, self.session_name = self.get_names()
        self.tipo = 2
        
    def get_names(self):
        return 'page_impd_guia', 'impd-guias'
    
    def get_documents(self, query):
        docs = models.ImpdGuiaRemision.objects.filter(query)
        if self.get_razon_social() or self.get_identificacion():
            destinatarios = models.ImpdGRDestinatario.objects.filter(Q(identificacion_destinatario = self.get_identificacion()) | 
                            Q(razon_social_destinatario__icontains = self.get_razon_social()))
            guias_list = [d.guia_remision.pk for d in destinatarios if d.guia_remision]
            docs = docs.filter(pk__in = guias_list)
        docs = docs.order_by('-fecha_creacion')
        print 'Guias encontradas:', docs.count()
        self.suma_documentos = 0
        return docs

class FiltroGuiasAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
        
    def process_filter(self, form):
        import forms
        try:           
            form = forms.ConsultaGuiasForm(deserialize_form(form))
            if form.is_valid():
                helper = FiltroGuiasHelper(self.request, form)
                documentos = helper.process()
                if documentos:
                    html = render_to_string('emisores/imprenta_digital/guiaremision/items-lista-guia.html', {'object_list': documentos})
                    self.dajax.assign('#guias', 'innerHTML', html)
                    self.dajax.assign('#cantidad', 'innerHTML', str(helper.cantidad))
                    self.dajax.assign('#suma', 'innerHTML', str(helper.suma_documentos))
                else:
                    self.dajax.assign('#guias', 'innerHTML', '')
                    self.dajax.assign('#cantidad', 'innerHTML', '0')
                    self.dajax.assign('#suma', 'innerHTML', '0')
                    self.dajax.alert('No se encontraron datos con esos terminos de consulta')
            else:
                print form.errors
                self.dajax.alert('Por favor ingrese terminos de consulta correctos')
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))
        
        return self.return_ajax(self.dajax)

class FiltroRetencionesHelper(FiltroComprobantesHelper):

    def __init__(self, request, form):
        self.request = request
        self.form = form
        self.filas = 5
        self.suma_documentos = 0
        self.cantidad = 0
        self.page_name, self.session_name = self.get_names()
        self.tipo = 3
        
    def get_names(self):
        return 'page_impd_retencion', 'impd-retenciones'
    
    def get_documents(self, query):
        docs = models.ImpdComproRetencion.objects.filter(query).order_by('-fecha_creacion')
        print 'Retenciones encontradas:', docs.count()
        self.suma_documentos = 0
        return docs

class FiltroRetencionesAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
        
    def process_filter(self, form):
        import forms
        try:           
            form = forms.ConsultaRetencionesForm(deserialize_form(form))
            if form.is_valid():
                helper = FiltroRetencionesHelper(self.request, form)
                documentos = helper.process()
                if documentos:
                    html = render_to_string('emisores/imprenta_digital/comproretencion/items-lista-retencion.html', {'object_list': documentos})
                    self.dajax.assign('#retenciones', 'innerHTML', html)
                    self.dajax.assign('#cantidad', 'innerHTML', str(helper.cantidad))
                    self.dajax.assign('#suma', 'innerHTML', str(helper.suma_documentos))
                else:
                    self.dajax.assign('#retenciones', 'innerHTML', '')
                    self.dajax.assign('#cantidad', 'innerHTML', '0')
                    self.dajax.assign('#suma', 'innerHTML', '0')
                    self.dajax.alert('No se encontraron datos con esos terminos de consulta')
            else:
                print form.errors
                self.dajax.alert('Por favor ingrese terminos de consulta correctos')
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))
        
        return self.return_ajax(self.dajax)

'''
----------------------------
NUEVO: NOTA DE CREDITO
----------------------------
'''

class FiltroNotasCreditoHelper(FiltroComprobantesHelper):

    def __init__(self, request, form):
        self.request = request
        self.form = form
        self.filas = 5
        self.suma_documentos = 0
        self.cantidad = 0
        self.page_name, self.session_name = self.get_names()
        self.tipo = 3
        
    def get_names(self):
        return 'page_impd_nota_credito', 'impd-nota_credito'
    
    def get_documents(self, query):
        docs = models.ImpdNotaCredito.objects.filter(query).order_by('-fecha_creacion')
        print 'Notas de Credito encontradas:', docs.count()
        self.suma_documentos = 0
        return docs

class FiltroNotasCreditoAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
        
    def process_filter(self, form):
        import forms
        try:           
            form = forms.ConsultaNotasCreditoForm(deserialize_form(form))
            if form.is_valid():
                helper = FiltroNotasCreditoHelper(self.request, form)
                documentos = helper.process()
                if documentos:
                    html = render_to_string('emisores/imprenta_digital/notacredito/items-lista-notacredito.html', {'object_list': documentos})
                    self.dajax.assign('#notascredito', 'innerHTML', html)
                    self.dajax.assign('#cantidad', 'innerHTML', str(helper.cantidad))
                    self.dajax.assign('#suma', 'innerHTML', str(helper.suma_documentos))
                else:
                    self.dajax.assign('#notascredito', 'innerHTML', '')
                    self.dajax.assign('#cantidad', 'innerHTML', '0')
                    self.dajax.assign('#suma', 'innerHTML', '0')
                    self.dajax.alert('No se encontraron datos con esos terminos de consulta')
            else:
                print form.errors
                self.dajax.alert('Por favor ingrese terminos de consulta correctos')
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))
        
        return self.return_ajax(self.dajax)

class IMPDNotaCreditoHelper(ComprobanteHelper):
    
    def __init__(self, request=None, formset=None, form=None, formset_adicional=None):
        self.formset = formset
        self.request = request
        if request:
            self.user = request.user
        else:
            self.user = None

        self.formset_adicional = formset_adicional
        self.tipo = 'NC'
    
    def calc_totals(self):
        try:
            print 'IMPDNotaCreditoHelper - Calculando Nota Credito Formset'
            instances = self.formset.save(commit=False)
            factura = None
            total_sin_impuestos = 0
            total_descuentos = 0
            #total_con_impuestos = 0
            for instance in instances:
                print '--> INSTANCE CALC', instance
                if isinstance(instance, models.ImpdItemNotaCredito):
                    '''
                    El subtotal es la cantidad por el precio unitario configurado del producto y la resta del descuento,
                    por lo general descuento es 0 asi que la resta es el mismo subtotal
                    '''
                    item_subtotal = (float(instance.cantidad) * float(instance.id_producto.precio_unitario)) - float(instance.descuento)
                    total_descuentos += float(instance.descuento)                    
                    impuestos_item = 0
                    
                    '''
                    Se calculan los impuestos del item en base a los impuestos configurados
                    del producto y el subtotal calculado (item_subtotal)
                    '''
                    for prod_imp in instance.id_producto.impdproductoimpuesto_set.all():
                        valor = float(prod_imp.tarifa) * 0.01 * float(item_subtotal)
                        impuestos_item += valor
                    
                    total_sin_impuestos += item_subtotal
                    #total_con_impuestos +=  float(item_subtotal) + float(impuestos_item)
        except Exception as e:
            traceback.print_exc()
            raise e        
        return total_sin_impuestos
    
    def save_detalles_adicionales(self):
        instances = self.formset_adicional.save()
    
    def update(self, entity):
        total_sin_impuestos = self.calc_totals()
        if total_sin_impuestos > 0:
            entity.total_sin_impuestos = total_sin_impuestos
            entity.save()
        
    def save(self, entity):
        print 'IMPDNotaCreditoHelper - Guardando Nota Credito...'
        instances = self.formset.save(commit=False)
        nota_credito = None
        subtotal = 0
        total_impuestos = 0
        total_con_impuestos = 0
        total_descuentos = 0

        for instance in instances:
            print '--> INSTANCE SAVING', instance
            if isinstance(instance, models.ImpdItemNotaCredito):
                '''
                El subtotal es la cantidad por el precio unitario configurado del producto y la resta del descuento,
                por lo general descuento es 0 asi que la resta es el mismo subtotal
                '''
                item_subtotal = (float(instance.cantidad) * float(instance.id_producto.precio_unitario)) - float(instance.descuento)
                total_descuentos += float(instance.descuento)                    
                impuestos_item = 0
                
                instance.save()
                '''
                Se calculan los impuestos del item en base a los impuestos configurados
                del producto y el subtotal calculado (item_subtotal)
                '''
                for prod_imp in instance.id_producto.impdproductoimpuesto_set.all():
                    impuesto_item_notacredito = models.ImpdItemNotaCreditoImpuesto()
                    impuesto_item_notacredito.id_item_nota_credito = instance
                    impuesto_item_notacredito.producto_impuesto = prod_imp
                    impuesto_item_notacredito.base_imponible = item_subtotal
                    impuesto_item_notacredito.valor = float(prod_imp.tarifa) * 0.01 * float(item_subtotal)
                    impuesto_item_notacredito.save(user = self.user)
                    impuestos_item += impuesto_item_notacredito.valor

                instance.total_sin_impuestos = item_subtotal
                instance.save(user = self.user)
        
                total_impuestos += impuestos_item
                subtotal += instance.total_sin_impuestos
                total_con_impuestos +=  float(item_subtotal) + float(impuestos_item)
            else:
                instance.save(user = self.user)
        
        if entity:
            entity.total_sin_impuestos = subtotal
            entity.save(user = self.user)
        
        print '--> GUARDANDO 4'
        self.formset.save_m2m()
        self.save_detalles_adicionales()
    
    def generar_archivo(self, id):
        notacredito = None
        try:
            notacredito = models.ImpdNotaCredito.objects.get(pk=id)
            xml_data = render_to_string('comprobantes/notacredito.html', {'entity': notacredito})
            ruta = tasks.get_directorio_entrada(notacredito.ruc_empresa)
            if ruta:
                file_name = self.get_file_name(notacredito)
                notacredito.codigo_original = file_name.replace('.XML','')
                notacredito.save()
                temporal_file_path = "media/imprenta-digital/notascredito/%s" % file_name
                self.upload_file(notacredito, xml_data, temporal_file_path)
                messages.success(self.request,
                                 'Nota Credito %s creada y enviada con exito al directorio de tipo %s, el proceso tomara un par de minutos.' % (
                                     notacredito.codigo_original, P.DIRECTORIO_ENTRADA))
            else:
                messages.error(self.request,
                               'La empresa seleccionada no tiene definido un directorio de tipo ' + P.DIRECTORIO_ENTRADA)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al procesar la factura: %s' % str(e1))
        return notacredito
    
    def ver_xml(self, id):
        try:
            return self.preview(models.ImpdNotaCredito.objects.get(pk=id))
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al previsualizar comprobante: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/notascredito/')
    
    def to_pdf(self, id):
        try:
            return self.convertir_pdf(models.ImpdNotaCredito.objects.get(pk=id))
        except Exception as e:
            messages.error(self.request, 'Error al generar pdf del comprobante: %s' % str(e))
        return HttpResponseRedirect('/imprenta-digital/notascredito/')

    def desactivar(self, id):
        entity = None
        try:
            entity = models.ImpdNotaCredito.objects.get(pk=id)
            entity.estado = mixins.get_inactive_status()
            entity.save()
            messages.success(self.request, 'Nota Credito %s deshabilitada.' % entity.secuencial)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al desactivar la nota de credito: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/notascredito/')

'''
----------------------------
NUEVO-FIN: NOTA DE CREDITO
----------------------------
'''

'''
----------------------------
NUEVO: NOTA DE DEBITO
----------------------------
'''
class FiltroNotasDebitoHelper(FiltroComprobantesHelper):

    def __init__(self, request, form):
        self.request = request
        self.form = form
        self.filas = 5
        self.suma_documentos = 0
        self.cantidad = 0
        self.page_name, self.session_name = self.get_names()
        self.tipo = 2
    
    def get_names(self):
        return 'page_impd_nota_debito', 'impd-notasdebito'
    
    def get_documents(self, query):
        docs = models.ImpdNotaDebito.objects.filter(query).order_by('-fecha_creacion')
        print 'Notas debito encontradas:', docs.count()
        self.suma_documentos = 0
        return docs

class FiltroNotasDebitoAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
    
    def process_filter(self, form):
        import forms
        try:           
            form = forms.ConsultaNotasDebitoForm(deserialize_form(form))
            if form.is_valid():
                helper = FiltroNotasDebitoHelper(self.request, form)
                documentos = helper.process()
                if documentos:
                    html = render_to_string('emisores/imprenta_digital/notadebito/items-lista-notadebito.html', {'object_list': documentos})
                    self.dajax.assign('#notasdebito', 'innerHTML', html)
                    self.dajax.assign('#cantidad', 'innerHTML', str(helper.cantidad))
                    self.dajax.assign('#suma', 'innerHTML', str(helper.suma_documentos))
                else:
                    self.dajax.assign('#notasdebito', 'innerHTML', '')
                    self.dajax.assign('#cantidad', 'innerHTML', '0')
                    self.dajax.assign('#suma', 'innerHTML', '0')
                    self.dajax.alert('No se encontraron datos con esos terminos de consulta')
            else:
                print form.errors
                self.dajax.alert('Por favor ingrese terminos de consulta correctos')
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))
        
        return self.return_ajax(self.dajax)

class IMPDNotaDebitoHelper(ComprobanteHelper):
    
    def __init__(self, request=None, formset=None, motivos_formset=None, formset_adicional=None):
        self.formset = formset
        self.request = request
        self.user = request.user
        self.motivos_formset = motivos_formset  
        self.formset_adicional = formset_adicional
        self.tipo = 'ND'
    
    def save(self, entity):
        print 'IMPDNotaDebitoHelper - Guardando nota debito, impuestos, motivos...'
        self.formset.save()        
        self.motivos_formset.save() 
        self.formset_adicional.save()
    
    def update(self, entity):
        pass
    
    def generar_archivo(self, id):
        notadebito = None
        try:
            notadebito = models.ImpdNotaDebito.objects.get(pk=id)
            xml_data = render_to_string('comprobantes/notadebito.html', {'entity': notadebito})
            ruta = tasks.get_directorio_entrada(notadebito.ruc_empresa)
            if ruta:
                file_name = self.get_file_name(notadebito)
                notadebito.codigo_original = file_name.replace('.XML','')
                notadebito.save()
                temporal_file_path = "media/imprenta-digital/notadebito/%s" % file_name
                self.upload_file(notadebito, xml_data, temporal_file_path)
                messages.success(self.request,
                                 'Nota Debito %s creada y enviada con exito al directorio de tipo %s, el proceso tomara un par de minutos.' % (
                                     notadebito.codigo_original, P.DIRECTORIO_ENTRADA))
            else:
                messages.error(self.request,
                               'La empresa seleccionada no tiene definido un directorio de tipo ' + P.DIRECTORIO_ENTRADA)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al procesar la nota de debito: %s' % str(e1))
        return notadebito
    
    def ver_xml(self, id):
        try:
            return self.preview(models.ImpdNotaDebito.objects.get(pk=id))
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al previsualizar comprobante: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/notasdebito/')
    
    def to_pdf(self, id):
        try:
            return self.convertir_pdf(models.ImpdNotaDebito.objects.get(pk=id))
        except Exception as e:
            messages.error(self.request, 'Error al generar pdf del comprobante: %s' % str(e))
        return HttpResponseRedirect('/imprenta-digital/notasdebito/')

    def desactivar(self, id):
        entity = None
        try:
            entity = models.ImpdNotaDebito.objects.get(pk=id)
            entity.estado = mixins.get_inactive_status()
            entity.save()
            messages.success(self.request, 'Nota Debito %s deshabilitada.' % entity.secuencial)
        except Exception as e1:
            traceback.print_exc()
            messages.error(self.request,
                           'Error al desactivar la nota de debito: %s' % str(e1))
        return HttpResponseRedirect('/imprenta-digital/notasdebito/')

'''
----------------------------
NUEVO-FIN: NOTA DE DEBITO
----------------------------
'''

class SaveAllHelper():
    
    def __init__(self, dajax, t_singular, t_plural, comprobante_helper=None, instance=None):
        self.dajax = dajax
        self.t_singular = t_singular
        self.t_plural = t_plural
        self.comprobante_helper = comprobante_helper
        self.instance = instance
        
    def saveAll(self, main_form, config_form, customer_form=None, *formset_list):
        try:
            savepoint = transaction.savepoint()
            config = config_form.save()
            
            if customer_form:
                customer = customer_form.save()
            else:
                customer = None
            
            if customer:
                entity = main_form.save(config, customer, commit=False)
            else:
                entity = main_form.save(config, commit=False)
            
            entity.save()
            
            for formset in formset_list:
                if formset: formset.instance = entity
            
            self.comprobante_helper.save(entity)
            
            if entity and not self.instance:
                entity.secuencial = config_form.get_secuencial()
                entity.secuencial_number = int(entity.secuencial)
                entity.save()
            
            transaction.savepoint_commit(savepoint)
            return self.ajax_response()
        except Exception as e:
            print 'saveAll - Error', e
            transaction.savepoint_rollback(savepoint)
            traceback.print_exc()
            self.dajax.script('bootbox.alert("Error al guardar: %s.");' % str(e))
        return self.dajax.json()
    
    def ajax_response(self):
        self.dajax.assign('#crear_%s_error_list' % self.t_singular, 'innerHTML', '')
        self.dajax.remove_css_class('body input', 'field_error')
        self.dajax.script("window.location = '/imprenta-digital/%s/';" %  self.t_plural);
        self.dajax.script('hideWait();')
        return self.dajax.json()
    
    def set_form_errors(self, form):
        for error in form.errors:
            self.dajax.add_css_class('#id_%s' % error, 'field_error')

    def set_formset_errors(self, formset):
        print 'ERRORES FORM SET', formset.errors
        for error in formset.errors:
            for field in error:
                self.dajax.add_css_class('#id_%s' % field, 'field_error')
    
    def manage_errors(self, main_form, config_form=None, second_form=None, *formset_list):
        self.dajax.assign('#crear_%s_error_list' % self.t_singular, 'innerHTML', '')
        self.dajax.remove_css_class('body input', 'field_error')
        self.set_form_errors(main_form)
        if config_form: self.set_form_errors(config_form)
        
        if second_form:
            self.set_form_errors(second_form)
        
        if formset_list:
            for formset in formset_list:
                if formset:
                    self.set_formset_errors(formset)
        
        context = {}
        context['form'] = main_form
        if config_form: context['config_form'] = config_form
        
        if second_form:
            import forms
            if isinstance(second_form, forms.ImpdGuiaRemisionDetalleDestinatarioForm):
                context['detalle_destinatario_form'] = second_form
            elif isinstance(second_form, forms.ClienteForm):
                context['customer_form'] = second_form
        
        if formset_list:
            index = 1
            for formset in formset_list:
                context['formset%d' % index] = formset
                index += 1
        
        html = render_to_string('emisores/imprenta_digital/messages.html', context)
        self.dajax.assign('#crear_%s_error_list' % self.t_singular, 'innerHTML', html)
        self.dajax.script(' $(window).scrollTop(10);')
        return self.dajax.json()
