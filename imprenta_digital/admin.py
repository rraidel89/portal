from django.contrib import admin
from django.conf.urls import patterns

from django.contrib import messages
from django.template.loader import render_to_string
from xml.etree import ElementTree as ET
from django.http import HttpResponseRedirect

import models
from helpers import secuencial_helper, IMPDGuiaRemisionHelper, IMPDComprobanteRetencionHelper
from innobee_portal import properties as P

from django.db import IntegrityError, transaction


import traceback
import datetime

'''
------------------------------------------------------------------------
Administradores para Imprenta Digital - COMUNES
------------------------------------------------------------------------
'''
def get_directorio_entrada(empresa):
    directorios = empresa.pordirectorioarchivosempresa_set.filter(
        tipo_directorio__nombre=P.DIRECTORIO_ENTRADA)
    if directorios.count() > 0:
        return directorios[0].ruta
    return None


class ImpdProductoDetalleAdicionalAdmin(admin.TabularInline):
    model = models.ImpdProductoDetalleAdicional
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    max_num = 8
    
class ImpdProductoImpuestoAdmin(admin.TabularInline):
    model = models.ImpdProductoImpuesto
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')

class ImpdProductoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'ruc_empresa', 'codigo_principal', 'codigo_secundario', 'descripcion',
        'precio_unitario', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    inlines = [ImpdProductoDetalleAdicionalAdmin, ImpdProductoImpuestoAdmin]
    raw_id_fields = ("ruc_empresa",)
    search_fields = ["codigo_principal","descripcion"]
    list_filter = ['ruc_empresa',]


class ImpdClienteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'ruc_empresa', 'tipo_identificacion', 'identificacion',
        'razon_social', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    raw_id_fields = ("ruc_empresa",)

class ImpdFacturaConfiguracionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'ruc_empresa', 'descripcion', 'establecimiento', 'punto_emision', 'moneda', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    raw_id_fields = ("ruc_empresa",)

'''
------------------------------------------------------------------------
Administradores para Imprenta Digital - FACTURAS
------------------------------------------------------------------------
'''

class ImpdItemFacturaAdmin(admin.TabularInline):
    model = models.ImpdItemFactura
    raw_id_fields = ("id_producto",)
    exclude = (
        'total_sin_impuestos', 'fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_actualizacion', 'estado')
    max_num = 30

class ImpdFacturaInformacionAdicionalAdmin(admin.TabularInline):
    model = models.ImpdFacturaInformacionAdicional
    exclude = ('fecha_creacion', 'fecha_actualizacion',
        'usuario_creacion', 'usuario_actualizacion', 'estado')
    max_num = 10

class ImpdFacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'ruc_empresa', 'secuencial', 'codigo_original', 'id_cliente', 'id_configuracion', 'fecha_emision',
                    'total_sin_impuestos', 'descuento', 'impuestos', 'total',
                    'fecha_actualizacion', 'estado', 'get_process')
    exclude = ('secuencial', 'codigo_original', 'total_sin_impuestos', 'descuento', 'impuestos', 'total',
               'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion')
    inlines = [ImpdItemFacturaAdmin, ImpdFacturaInformacionAdicionalAdmin]
    raw_id_fields = ("ruc_empresa", "id_cliente", "id_configuracion")
    search_fields = ["secuencial","id_cliente__identificacion","id_cliente__razon_social"]
    list_filter = ['ruc_empresa','fecha_actualizacion']

    def save_formset(self, request, form, formset, change):
        try:
            print 'ImpdFacturaAdmin - Guardando Factura Formset'
            user = request.user
            savepoint = transaction.savepoint()
            instances = formset.save(commit=False)
            factura = None
            subtotal = 0
            total_con_impuestos = 0
            total_descuentos = 0
            total_impuestos = 0
            for instance in instances:
                print '--> INSTANCE SAVING', instance
                if isinstance(instance, models.ImpdItemFactura):
                    factura = instance.id_factura
                    '''
                    El subtotal es la cantidad por el precio unitario configurado del producto y la resta del descuento,
                    por lo general descuento es 0 asi que la resta es el mismo subtotal
                    '''
                    item_subtotal = float(instance.cantidad) * float(instance.id_producto.precio_unitario) - float(instance.descuento)
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
                        impuesto_item_factura.save(user = user)
                        impuestos_item += impuesto_item_factura.valor
    
                    instance.total_sin_impuestos = item_subtotal
                    instance.save(user = user)
                    print '--> SAVED!'
    
                    total_impuestos += impuestos_item
                    subtotal += instance.total_sin_impuestos
                    total_con_impuestos +=  float(item_subtotal) + float(impuestos_item)
                else:
                    instance.save(user = user)
            '''
            La factura se guarda con los totales anteriormente calculados, ademas se obtiene
            el siguiente secuencial. El codigo original se queda en blanco hasta la generacion
            de la factura XML
            '''
            if factura:
                factura.secuencial = secuencial_helper.get_next_secuencial_factura(factura)
                factura.secuencial_number = int(factura.secuencial)
                factura.total_sin_impuestos = subtotal
                factura.descuento = total_descuentos
                factura.impuestos = total_impuestos
                factura.total = total_con_impuestos + float(factura.propina)
                factura.save(user = user)
            
            formset.save_m2m()
            transaction.savepoint_commit(savepoint)
        except Exception as e:
            transaction.savepoint_rollback(savepoint)
            traceback.print_exc()
            raise e

    def get_urls(self):
        urls = super(ImpdFacturaAdmin, self).get_urls()
        custom_urls = patterns('',
                               (r'(?P<id>\d+)/process/$',
                                self.admin_site.admin_view(self.process_view)),
        )
        return custom_urls + urls

    def get_process(self, obj):
        return '<a href="/admin/imprenta_digital/impdfactura/%d/process/">Procesar</a>' % (
            obj.id)

    get_process.short_description = 'Procesar'
    get_process.allow_tags = True

    def process_view(self, request, id):
        factura = None
        try:
            factura = models.ImpdFactura.objects.get(pk=id)
            xml_data = render_to_string('comprobantes/factura.html',
                                        {'factura': factura})
            tree = ET.XML(xml_data)
            ahora = datetime.datetime.now()

            ruta = get_directorio_entrada(factura.ruc_empresa)
            if ruta:
                if not ruta.endswith('/'): ruta += '/'
                file_name = 'FE%s%s%s%s%s%s%s%s.XML' % (
                    str(factura.ruc_empresa),
                    factura.id_configuracion.establecimiento,
                    factura.id_configuracion.punto_emision,
                    factura.secuencial,
                    ahora.strftime("%d%m%Y"), ahora.hour, ahora.minute,
                    ahora.second)
                factura.codigo_original = file_name.replace('.XML','')
                factura.save()
                complete_file_path = "%s%s" % (ruta, file_name)
                print 'ImpdFacturaAdmin - Creando Archivo', complete_file_path
                with open(complete_file_path, "w") as f:
                    f.write(ET.tostring(tree))
                messages.success(request,
                                 'Factura %d creada y enviada con exito al directorio de tipo %s, el proceso tomara un par de minutos.' % (
                                     factura.id, P.DIRECTORIO_ENTRADA))
            else:
                messages.error(request,
                               'La empresa seleccionada no tiene definido un directorio de tipo ' + P.DIRECTORIO_ENTRADA)
        except Exception as e1:
            traceback.print_exc()
            messages.error(request,
                           'Error al procesar la factura: %s' % str(e1))

        return HttpResponseRedirect("/admin/imprenta_digital/impdfactura/")

admin.site.register(models.ImpdProducto, ImpdProductoAdmin)
admin.site.register(models.ImpdCliente, ImpdClienteAdmin)
admin.site.register(models.ImpdFacturaConfiguracion, ImpdFacturaConfiguracionAdmin)
admin.site.register(models.ImpdFactura, ImpdFacturaAdmin)

'''
------------------------------------------------------------------------
Administradores para Imprenta Digital - GUIAS DE REMISION
------------------------------------------------------------------------
'''

class ImpdGRDetalleDestinatarioAdmin(admin.TabularInline):
    model = models.ImpdGRDetalleDestinatario
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    max_num = 30
    
class ImpdGRInformacionAdicionalAdmin(admin.TabularInline):
    model = models.ImpdGRInformacionAdicional
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    max_num = 30

class ImpdGuiaRemisionAdmin(admin.ModelAdmin):
    list_display = ('id', 'secuencial', 'codigo_original', 'id_configuracion', 'fecha_emision',
                    'direccion_partida', 'razon_social_transportista', 'ruc_transportista', 'fecha_inicio_transporte',
                    'fecha_fin_transporte','placa', 'fecha_actualizacion', 'estado', 'get_process')
    exclude = ('secuencial', 'secuencial_number', 'codigo_original', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion')
    inlines = [ImpdGRDetalleDestinatarioAdmin, ImpdGRInformacionAdicionalAdmin]
    raw_id_fields = ("ruc_empresa", "id_configuracion")
    
    def save_formset(self, request, form, formset, change):
        helper = IMPDGuiaRemisionHelper(request, formset)
        helper.save_guia_remision()
    
    def get_urls(self):
        urls = super(ImpdGuiaRemisionAdmin, self).get_urls()
        custom_urls = patterns('',
                               (r'(?P<id>\d+)/process/$',
                                self.admin_site.admin_view(self.process_view)),
        )
        return custom_urls + urls

    def get_process(self, obj):
        return '<a href="/admin/imprenta_digital/impdguiaremision/%d/process/">Procesar</a>' % (
            obj.id)

    get_process.short_description = 'Procesar'
    get_process.allow_tags = True

    def process_view(self, request, id):
        helper = IMPDGuiaRemisionHelper(request)
        helper.generar_archivo(id)
        return HttpResponseRedirect("/admin/imprenta_digital/impdguiaremision/")

admin.site.register(models.ImpdGuiaRemision, ImpdGuiaRemisionAdmin)

class ImpdGRDestinatarioAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'identificacion_destinatario', 'razon_social_destinatario',
        'direccion_destinatario', 'estado')
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')

admin.site.register(models.ImpdGRDestinatario, ImpdGRDestinatarioAdmin)

'''
------------------------------------------------------------------------
Administradores para Imprenta Digital - COMPROBANTES DE RETENCION
------------------------------------------------------------------------
'''

class ImpdCRETImpuestosAdmin(admin.TabularInline):
    model = models.ImpdCRETImpuestos
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    max_num = 80
    
class ImpdCRETInformacionAdicionalAdmin(admin.TabularInline):
    model = models.ImpdCRETInformacionAdicional
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    max_num = 5

class ImpdComproRetencionAdmin(admin.ModelAdmin):
    list_display = ('id', 'secuencial', 'codigo_original', 'id_configuracion', 'fecha_emision',
                    'periodo_fiscal', 'fecha_actualizacion', 'estado', 'get_process')
    exclude = ('secuencial', 'secuencial_number', 'codigo_original', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion')
    inlines = [ImpdCRETImpuestosAdmin, ImpdCRETInformacionAdicionalAdmin]
    raw_id_fields = ("ruc_empresa", "id_configuracion")
    
    def save_formset(self, request, form, formset, change):
        helper = IMPDComprobanteRetencionHelper(request, formset=formset)
        helper.save_retencion()
    
    def get_urls(self):
        urls = super(ImpdComproRetencionAdmin, self).get_urls()
        custom_urls = patterns('',
                               (r'(?P<id>\d+)/process/$',
                                self.admin_site.admin_view(self.process_view)),
        )
        return custom_urls + urls

    def get_process(self, obj):
        return '<a href="/admin/imprenta_digital/impdguiaremision/%d/process/">Procesar</a>' % (
            obj.id)

    get_process.short_description = 'Procesar'
    get_process.allow_tags = True

    def process_view(self, request, id):
        helper = IMPDComprobanteRetencionHelper(request)
        helper.generar_archivo(id)
        return HttpResponseRedirect("/admin/imprenta_digital/impdguiaremision/")

admin.site.register(models.ImpdComproRetencion, ImpdComproRetencionAdmin)