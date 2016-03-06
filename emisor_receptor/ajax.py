#import simplejson
from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from dajaxice.core import dajaxice_functions

from django.template.loader import render_to_string
from django.utils import simplejson
from django.template.context import RequestContext
from django.db.models.query_utils import Q

from core import models as core_models
from core import mixins as core_mixins
from emisor_receptor import forms as er_forms

from views import get_pagination_page
import traceback
import helpers
import datetime

def check_watch(request, variable):
    print 'check_watch - Actualizando notificaciones ', variable, '...' 
    #dajax = Dajax()
    
    perfil_usuario = request.user.get_profile()
    if perfil_usuario.ruc_empresa is not None:
        queries_notificacion = [
        Q(identificacion_receptor=perfil_usuario.ruc_empresa)]
    else:
        queries_notificacion = \
            [Q(identificacion_receptor=perfil_usuario.identificacion)]

    query_notificacion = queries_notificacion.pop()
    for item in queries_notificacion:
        query_notificacion &= item

    notificaciones = core_models.Documento.objects.filter(query_notificacion).\
        filter(Q(leido=False) | Q(leido__isnull=True))
    
    for notificacion in notificaciones:
        notificacion.leido=True
        notificacion.save()
    
    print 'check_watch - Se cambiaron ',len(notificaciones),' notificaciones...'
        
    return simplejson.dumps({'variable':variable})

dajaxice_functions.register(check_watch)

def cargar_sub_categorias(request, nombre_categoria=None):
    subcategorias_json = []
    if nombre_categoria:
        print 'cargar_sub_categorias - Filtrando por categoria', nombre_categoria
        subcategorias = core_models.SubcategoriaProducto.objects.filter(categoria = nombre_categoria)
        print 'cargar_sub_categorias - Encontrados', len(subcategorias), 'elementos'
        for subcategoria in subcategorias:
            subcategorias_json.append({
                'id' : subcategoria.nombre,
                'value'  : subcategoria.nombre
            })
    else:
        print 'cargar_sub_categorias - No se ha dado el nombre de la categoria'
    return simplejson.dumps({'subcategorias':subcategorias_json})

dajaxice_functions.register(cargar_sub_categorias)

def cargar_sub_categorias_empresa(request, nombre_categoria=None):
    subcategorias_json = []
    if nombre_categoria:
        print 'cargar_sub_categorias_empresa - Filtrando por categoria', nombre_categoria
        subcategorias = core_models.PorSubcategoria.objects.filter(categoria = nombre_categoria)
        print 'cargar_sub_categorias_empresa - Encontrados', len(subcategorias), 'elementos'
        for subcategoria in subcategorias:
            subcategorias_json.append({
                'id' : subcategoria.nombre,
                'value'  : subcategoria.nombre
            })
    else:
        print 'cargar_sub_categorias_empresa - No se ha dado el nombre de la categoria'
    return simplejson.dumps({'subcategorias':subcategorias_json})

dajaxice_functions.register(cargar_sub_categorias_empresa)

def cargar_provincias_pais(request, nombre_pais=None):
    provincias_json = []
    if nombre_pais:
        print 'cargar_provincias_pais - Filtrando por pais', nombre_pais
        provincias = core_models.PorProvincia.objects.filter(pais = nombre_pais)
        print 'cargar_provincias_pais - Encontrados', len(provincias), 'elementos'
        for provincia in provincias:
            provincias_json.append({
                'id' : provincia.nombre,
                'value'  : provincia.nombre
            })
    else:
        print 'cargar_provincias_pais - No se ha dado el nombre del pais'
    return simplejson.dumps({'provincias':provincias_json})

dajaxice_functions.register(cargar_provincias_pais)

def cargar_ciudades_provincia(request, nombre_provincia=None):
    ciudades_json = []
    if nombre_provincia:
        print 'cargar_ciudades_provincia - Filtrando por provincia', nombre_provincia
        ciudades = core_models.PorCiudad.objects.filter(provincia = nombre_provincia)
        print 'cargar_ciudades_provincia - Encontrados', len(ciudades), 'elementos'
        for ciudad in ciudades:
            ciudades_json.append({
                'id' : ciudad.nombre,
                'value' : ciudad.nombre
            })
    else:
        print 'cargar_ciudades_provincia - No se ha dado el nombre de la provincia'
    return simplejson.dumps({'ciudades':ciudades_json})

dajaxice_functions.register(cargar_ciudades_provincia)

def agregar_bandeja_impresion(request, entity_id, entity_type):
    dajax = Dajax()
    try:
        if entity_id and entity_type:
            print 'agregar_bandeja_impresion - Leyendo entidad de tipo', entity_type
            entidad = None
            if entity_type == 'cupon':            
                entidad = core_models.Cupon.objects.get(id = entity_id)
                if entidad.nro_impresiones is None:
                    entidad.nro_impresiones = 0
                entidad.nro_impresiones += 1
                entidad.save()
            
            html = None
            if entidad:
                html = render_to_string('webparts/print_render/%s.html' % entity_type, {'entidad': entidad})
            else:
                print 'agregar_bandeja_impresion - Entidad No Existe', entity_id,  entity_type
            
            if html:
                try:
                    bandeja_impresion = request.session['BANDEJA_IMPRESION']
                    if len(bandeja_impresion) < 10:
                        bandeja_impresion.append(html)
                    else:
                        bandeja_impresion = None
                except Exception as e:
                    print 'agregar_bandeja_impresion - Error', e
                    bandeja_impresion = []
                    bandeja_impresion.append(html)
                
                if bandeja_impresion:
                    request.session['BANDEJA_IMPRESION'] = bandeja_impresion
                    dajax.script("mostrarModalImpresion(%d);" % len(bandeja_impresion))
                    print 'agregar_bandeja_impresion - Bandeja de impresion actualizada con exito'
                else:
                    dajax.script("mostrarWarningModalImpresion();")
                    print 'agregar_bandeja_impresion - Bandeja de impresion llena'
            else:
                print 'agregar_bandeja_impresion - Entidad sin HTML'
        else:
            print 'agregar_bandeja_impresion - Error - Se requieren id y tipo'
    except Exception as ex:
        print 'agregar_bandeja_impresion - Fatal', ex
    return dajax.json()

dajaxice_functions.register(agregar_bandeja_impresion)

def limpiar_bandeja_impresion(request):
    dajax = Dajax()
    try:
        del request.session['BANDEJA_IMPRESION']
        print 'limpiar_bandeja_impresion - Bandeja de impresion borrada con exito'
    except Exception as e:
        print 'limpiar_bandeja_impresion - Error', e
    return dajax.json()

dajaxice_functions.register(limpiar_bandeja_impresion)

def banner_click(request, banner_id):
    dajax = Dajax()
    try:
        print 'banner_click - Procesando click al banner', banner_id
        banner = core_models.Banner.objects.get(id_banner = banner_id)
        if banner.nro_clicks is None:
            banner.nro_clicks = 0
        banner.nro_clicks += 1
        banner.save()
        #dajax.script("window.open('%s');" % banner.url_banner_apunta)
    except Exception as e:
        print 'banner_click - Error', e
    return dajax.json()

dajaxice_functions.register(banner_click)

def aceptar_comprobante_recibido(request, tipo_comprobante, comprobante_id, observaciones):
    dajax = Dajax()
    try:
        operador = request.user.get_profile()
        docs = core_models.Documento.objects.filter(pk=comprobante_id, tipo_comprobante=tipo_comprobante)
        estado = core_mixins.get_authorized_notif_status()
        if estado:
            print 'aceptar_comprobante_recibido - Estableciendo', docs.count(), 'comprobante a estado', estado.nombre
            docs.update(estado_notificacion=estado, observaciones=observaciones[:80], aprobado_por = operador.get_nombre_completo()[:32])
        else:
            print 'aceptar_comprobante_recibido - No hay estado aceptado'
        dajax.script("activar_autorizacion_comprobante('%s','%s');" % (tipo_comprobante, comprobante_id))
    except Exception as e:
        print 'aceptar_comprobante_recibido - Error', e
    return dajax.json()
    
dajaxice_functions.register(aceptar_comprobante_recibido)

def rechazar_comprobante_recibido(request, tipo_comprobante, comprobante_id, observaciones, email_rechazo):
    dajax = Dajax()
    try:
        operador = request.user.get_profile()
        docs = core_models.Documento.objects.filter(pk=comprobante_id, tipo_comprobante=tipo_comprobante)
        estado = core_mixins.get_rejected_notif_status()
        if estado:
            print 'rechazar_comprobante_recibido - Estableciendo', docs.count(), 'comprobante a estado', estado.nombre
            docs.update(estado_notificacion=estado, observaciones=observaciones[:80])
            try:
                from innobee_util import util
                for doc in docs:
                    email_remitente = email_rechazo.strip()
                    if email_remitente == '':
                        email_remitente = doc.email_remitente
                    util.enviar_email_rechazo_comprobante(operador.get_nombre_completo(), email_remitente,
                               doc.observaciones, doc.razon_social_emisor, str(doc.monto_total), doc.secuencial)
            except Exception as e:
                dajax.alert('El comprobante fue rechazado pero no se pudo enviar el correo al remitente debido a: %s' % str(e))
        else:
            print 'rechazar_comprobante_recibido - No hay estado rechazado'
        dajax.script("activar_rechazo_comprobante('%s','%s');" % (tipo_comprobante, comprobante_id))
    except Exception as e:
        print 'rechazar_comprobante_recibido - Error', e
    return dajax.json()
    
dajaxice_functions.register(rechazar_comprobante_recibido)

def filter_emitidos_form(request, form):
    helper = helpers.FiltroDocumentoAjaxHelper(request, 'emitidos')
    return helper.process_filter(form)

dajaxice_functions.register(filter_emitidos_form)

def filter_recibidos_form(request, form):
    helper = helpers.FiltroDocumentoAjaxHelper(request, 'recibidos')
    return helper.process_filter(form)

dajaxice_functions.register(filter_recibidos_form)

def filter_cargados_form(request, form):
    helper = helpers.FiltroDocumentoAjaxHelper(request, 'cargados')
    return helper.process_filter(form)

dajaxice_functions.register(filter_cargados_form)

def filter_banners_form(request, form):
    helper = helpers.FiltroBannerAjaxHelper(request)
    return helper.process_filter(form)

dajaxice_functions.register(filter_banners_form)

def filter_cupones_form(request, form):
    helper = helpers.FiltroCuponAjaxHelper(request)
    return helper.process_filter(form)

dajaxice_functions.register(filter_cupones_form)

def filter_productos_form(request, form):
    helper = helpers.FiltroProductoAjaxHelper(request)
    return helper.process_filter(form)

dajaxice_functions.register(filter_productos_form)

def filter_campanias_form(request, form):
    helper = helpers.FiltroCampaniasAjaxHelper(request)
    return helper.process_filter(form)

dajaxice_functions.register(filter_campanias_form)

def filter_campanias_sms_form(request, form):
    helper = helpers.FiltroCampaniasAjaxHelper(request)
    return helper.process_filter_sms(form)

dajaxice_functions.register(filter_campanias_sms_form)

def filter_campanias_email_form(request, form):
    helper = helpers.FiltroCampaniasAjaxHelper(request)
    return helper.process_filter_email(form)

dajaxice_functions.register(filter_campanias_email_form)

def filter_reporte_general_form(request, form):
    helper = helpers.FiltroReportesAjaxHelper(request)
    return helper.process_filter_general(form)

dajaxice_functions.register(filter_reporte_general_form)

def filter_reporte_individual_form(request, form):
    helper = helpers.FiltroReportesAjaxHelper(request)
    return helper.process_filter_individual(form)

dajaxice_functions.register(filter_reporte_individual_form)

def pagination(request, p, p_type):
    try:
        page, session_name = helpers.get_names(p_type)
        try:
            filas = request.session[session_name + 'filas']
        except Exception as e:
            filas = 5

        items = request.session[session_name]
        items = get_pagination_page(request, page, items, filas, p)
        helper = helpers.FiltroDocumentoAjaxHelper(request, p_type)
        return helper.print_items(items)
    except Exception as e:
        traceback.print_exc()
        dajax = Dajax()
        dajax.alert('NO HAY RESULTADOS: '+str(e))
        dajax.script('hideWait();')
        return dajax.json()

dajaxice_functions.register(pagination)

def cambiar_estado_comprobante(request, tipo_comprobante, comprobante_id, codigo_anulacion):
    dajax = Dajax()
    try:
        estado = helpers.cambiar_estado_comprobante_emitido(request.user.username, tipo_comprobante, comprobante_id, codigo_anulacion)
        if estado:
            dajax.script("location.reload();")
    except Exception as e:
        print 'cambiar_estado_comprobante - Error', e
    return dajax.json()
    
dajaxice_functions.register(cambiar_estado_comprobante)

def reenotificar(request, tipo_comprobante, comprobante_id, emails_notificacion):
    dajax = Dajax()
    try:
        if helpers.renotificar_comprobante_emitido(request.user.username, tipo_comprobante, comprobante_id, emails_notificacion):
            dajax.script("restaurar_renotificacion();")
        else:
            dajax.script("bootbox.alert('No pudo re-notificarse el comprobante.');")
    except Exception as e:
        print 'reenotificar - Error', e

    dajax.script('hideWait();')
    return dajax.json()

dajaxice_functions.register(reenotificar)
