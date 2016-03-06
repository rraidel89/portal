
from django.db.models.query_utils import Q
from django.db.models import Sum, Count, Max
from django.template.loader import render_to_string

from dajax.core import Dajax
from dajaxice.utils import deserialize_form

from emisor_receptor import forms as er_forms
from core import models as core_models
from core import mixins as core_mixins

from innobee_portal import properties as P

from django.conf import settings

from itertools import chain
from core.helper import FiltroHelper, FiltroAjaxHelper

from innobee_util import util

import traceback
import datetime

hoy = datetime.datetime.now()
hoy = hoy.strftime('%Y-%m-%d')

def get_names(name):
        if name == 'emitidos':
            return 'page_emit', 'documentos_emitidos'
        elif name == 'recibidos':
            return 'page_recib', 'documentos_recibidos'
        elif name == 'cargados':
            return 'page', 'documentos_cargados'

class FiltroDocumentoHelper(FiltroHelper):

    def __init__(self, request=None, form=None, type_name=None):
        self.request = request
        self.form = form
        self.filas = 5
        self.suma_documentos = 0
        self.cantidad = 0
        if type_name:
            self.page_name, self.session_name = get_names(type_name)
            print 'FILTRO PARA', self.session_name
    
    def get_common_query(self, queries, start_date, end_date, tipo_doc, filas_docs):
        self.get_dates_query(queries, start_date, end_date)
        if self.cleaned_data[tipo_doc]: queries += [Q(tipo_comprobante=self.cleaned_data[tipo_doc])]
        #print 'LEYENDO FILAS', self.cleaned_data
        self.filas = self.cleaned_data[filas_docs]
        self.request.session[self.session_name + 'filas'] = self.filas
        return queries

    def disable_dupplicates(self):
        unique_fields = ['ruc_emisor', 'tipo_comprobante', 'establecimiento', 'pto_emision', 'secuencial', 'clave_acceso']

        duplicates = (core_models.Documento.objects.values(*unique_fields)
                                     .order_by()
                                     .annotate(max_id = Max('id'),
                                               count_id = Count('id'))
                                     .filter(count_id__gt=1,estado=core_mixins.get_active_status()))

        if len(duplicates) > 0:
            print '** >>>>>>> Deshabilitando', len(duplicates), ' DUPLICADOS'
            for duplicate in duplicates:
                #print '-------------------> DESHABILITANDO', duplicate['tipo_comprobante'], duplicate['establecimiento'],\
                #    duplicate['pto_emision'],duplicate['secuencial']
                (core_models.Documento.objects.filter(**{x: duplicate[x] for x in unique_fields})
                                .exclude(id=duplicate['max_id'])
                                .update(estado = core_mixins.get_inactive_status()))

            print '<<<<<<< **Deshabilitados', len(duplicates), ' DUPLICADOS'
        else:
            print '***** NO HAY DUPLICADOS A DESACTIVAR *****'

        return len(duplicates)

    def get_query_emitidos(self):
        queries = [Q(ruc_emisor=self.get_identificacion_usuario())]
        self.estado_filtro = None
        try:
            self.cleaned_data = self.form.cleaned_data.copy()
            self.get_common_query(queries, 'em_fecha_desde', 'em_fecha_hasta', 'em_tipo_documento', 'em_filas_emitidos')
            if self.cleaned_data['em_establecimiento']:
                queries += [Q(establecimiento=self.cleaned_data['em_establecimiento'])]
            if self.cleaned_data['em_puntoemi']:
                queries += [Q(pto_emision=self.cleaned_data['em_puntoemi'])]
            if self.cleaned_data['em_secuencial']:
                queries += [Q(secuencial=self.cleaned_data['em_secuencial'])]
            if self.cleaned_data['em_estado'] and self.cleaned_data['em_estado'] != '---':
                queries += [Q(estado=self.cleaned_data['em_estado'])]
                self.estado_filtro = self.cleaned_data['em_estado']
            if self.cleaned_data['em_cliente']:  queries += [Q(razon_social_receptor__icontains=self.cleaned_data['em_cliente']) |
                                                        Q(identificacion_receptor = self.cleaned_data['em_cliente'])]
        except Exception as e:
            print 'get_query_emitidos - Error:', e
    
        return self.build_query(queries)
    
    def get_query_recibidos(self):
        queries = [Q(identificacion_receptor=self.get_identificacion_usuario())]
        try:
            print 'Extrayendo documentos recibidos'
            self.cleaned_data = self.form.cleaned_data.copy()
            self.get_common_query(queries, 'fecha_desdeR', 'fecha_hastaR', 'tipo_documentoR', 'filas_recibidos')
            if self.cleaned_data['numeroR']: queries += [Q(secuencial=self.cleaned_data['numeroR'])]
            if self.cleaned_data['emisorR']: queries += [Q(razon_social_emisor__icontains=self.cleaned_data['emisorR']) |
                                                        Q(ruc_emisor=self.cleaned_data['emisorR'])]
            if self.cleaned_data['aprobado_porR']: queries += [Q(aprobado_por__icontains=self.cleaned_data['aprobado_porR'])]
            if self.cleaned_data['fuenteR']:
                queries += [Q(fuente_generacion=self.cleaned_data['fuenteR'])]
        except Exception as e:
            print 'get_query_recibidos - Error:', e

        return self.build_query(queries)
    
    def get_query_cargados(self):
        queries = [Q(buzon__identificacion=self.get_identificacion_usuario())]
        try:
            self.cleaned_data = self.form.cleaned_data.copy()
            #print 'Para QUERY CARGADOS', self.cleaned_data
            if self.cleaned_data['carg_fecha']: queries += [Q(fecha_emision=self.cleaned_data['carg_fecha'])]
            if self.cleaned_data['carg_tipo_comprobante']: queries += [Q(tipo_comprobante=self.cleaned_data['carg_tipo_comprobante'])]
            if self.cleaned_data['carg_numero']: queries += [Q(numero_comprobante=self.cleaned_data['carg_numero'])]
            if self.cleaned_data['carg_emisor']: queries += [Q(razon_social_emisor__icontains=self.cleaned_data['carg_emisor']) |
                                                        Q(ruc_emisor=self.cleaned_data['carg_emisor'])]
        except Exception as e:
            print 'get_query_cargados - Error:', e

        return self.build_query(queries)
    
    def get_documents(self, query):
        if self.session_name == 'documentos_emitidos':
            return core_models.Documento.objects.filter(query).values('id','tipo_comprobante', 'ruc_emisor', 'codigo_original').distinct()
        elif self.session_name == 'documentos_recibidos':
            return core_models.Documento.objects.filter(query).values('id','tipo_comprobante', 'ruc_emisor', 'codigo_original').distinct()
        elif self.session_name == 'documentos_cargados':
            return core_models.BuzDocumento.objects.filter(query).extra(select={'codigo_original': 'numero_autorizacion'})\
                    .values('id','tipo_comprobante', 'ruc_emisor', 'codigo_original').distinct()
        
    def get_documents_related(self):
        if self.session_name == 'documentos_emitidos':
            return core_models.Documento.objects.select_related('ciudad', 'estado', 'fuente_generacion')
        elif self.session_name == 'documentos_recibidos':
            return core_models.Documento.objects.select_related('ciudad', 'estado', 'fuente_generacion')
        elif self.session_name == 'documentos_cargados':
            return core_models.BuzDocumento.objects.select_related('ciudad', 'estado', 'fuente_generacion', 'buzon')
    
    def process(self):
        query = None
        if self.session_name == 'documentos_emitidos':
            #self.disable_dupplicates()
            query = self.get_query_emitidos()
            print 'QUERY EMITIDOS', query
        elif self.session_name == 'documentos_recibidos':
            query = self.get_query_recibidos()
            print 'QUERY RECIBIDOS', query
        elif self.session_name == 'documentos_cargados':
            query = self.get_query_cargados()
            print 'QUERY CARGADOS', query
        documentos = []
        if query:
            documentos_list1 = self.get_documents(query)
            
            documentos_ids = [dr['id'] for dr in documentos_list1]
            codigos_originales = [dr['codigo_original'] for dr in documentos_list1]                    
            documentos = self.get_documents_related().filter(query).filter(id__in = documentos_ids)
            
            if self.session_name == 'documentos_emitidos':
                if self.estado_filtro:
                    documentos = documentos.order_by('-fecha_creacion')
                else:
                    documentos = documentos.filter(Q(estado=core_mixins.get_active_status()) | Q(estado=core_mixins.get_anulado_status())).order_by('-fecha_creacion')
            else:
                documentos = documentos.filter(estado=core_mixins.get_active_status()).order_by('-fecha_creacion')
        
            self.request.session[self.session_name] = documentos
            
            self.suma_documentos = 0
            self.cantidad = documentos.count()

            for d in documentos:
                #if d.estado == core_mixins.get_active_status():
                if self.session_name == 'documentos_cargados':
                    self.suma_documentos += d.monto_comprobante
                else:
                    self.suma_documentos += d.monto_total
            
            self.request.session[self.session_name + 'cantidad'] = self.cantidad
            self.request.session[self.session_name + 'suma'] = self.suma_documentos
            
        return self.paginar(documentos)

class FiltroDocumentoAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request, type_name):
        self.dajax = Dajax()
        self.request = request
        self.type_name = type_name
        
    def process_filter(self, form):
        try:
            form_deserialized = deserialize_form(form)
            print form_deserialized
            if self.type_name == 'emitidos':
                form = er_forms.FiltroDocumento(form_deserialized)
            elif self.type_name == 'recibidos':
                form = er_forms.FiltroDocumentoRecibidos(form_deserialized)
            elif self.type_name == 'cargados':
                form = er_forms.FormComprobantesCargados(form_deserialized)
            if form.is_valid():
                helper = FiltroDocumentoHelper(self.request, form, self.type_name)
                documentos = helper.process()
                if documentos:
                    return self.print_items(documentos)
                else:
                    self.dajax.assign('#comprobantes-%s' % self.type_name, 'innerHTML', '')
                    self.dajax.assign('#cantidad-%s' % self.type_name, 'innerHTML', '0')
                    self.dajax.assign('#suma-%s' % self.type_name, 'innerHTML', '0')
                    self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'No se encontraron resultados')
            else:
                print form.errors
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))
        
        return self.return_ajax(self.dajax)
    
    def print_items(self, documentos, cantidad=None, suma=None):
        if cantidad is None or suma is None:
            page_name, session_name = get_names(self.type_name)
            try:
                cantidad = self.request.session[session_name + 'cantidad']
            except:
                cantidad = 0
            try:
                suma = self.request.session[session_name + 'suma']
            except:
                suma = 0
        
        html = render_to_string('webparts/%s_list_items.html' % self.type_name, {'documentos_%s' % self.type_name: documentos})
        self.dajax.assign('#comprobantes-%s' % self.type_name, 'innerHTML', html)
        self.dajax.assign('#cantidad-%s' % self.type_name, 'innerHTML', str(cantidad))
        self.dajax.assign('#suma-%s' % self.type_name, 'innerHTML', str(suma))
        html = render_to_string('webparts/common_pagination.html', {'docs_list': documentos, 'p_type' : self.type_name})
        if self.type_name == 'emitidos':
            self.dajax.assign('#emitidos-pagination', 'innerHTML', html)
        elif self.type_name == 'recibidos':
            self.dajax.assign('#recibidos-pagination', 'innerHTML', html)
        elif self.type_name == 'cargados':
            self.dajax.assign('#cargados-pagination', 'innerHTML', html)
        return self.return_ajax(self.dajax)

class FiltroBannerHelper(FiltroHelper):

    def __init__(self, request=None, form=None):
        self.request = request
        self.form = form
        self.filas = 5
        self.cantidad = 0
        self.page_name = 'page_banner'
        
    def get_next_banner(self):
        banners = core_models.Banner.objects.extra(where=["%s >= fecha_publicacion"],
            params=[hoy]).filter(Q(impresiones_restantes__isnull=True) |
            Q(impresiones_restantes__gt=0)).filter(estado=core_mixins.get_active_status()).order_by('?')
        
        if banners.count() > 0:
            banner = banners[0]
            if banner.impresiones_restantes is None:
                print 'Error - El banner mostrado no tiene impresiones'
                if banner.impresiones:
                    banner.impresiones_restantes = banner.impresiones
                else:
                    banner.impresiones_restantes = 1
            banner.impresiones_restantes -= 1
            banner.save()
        else:
            banner = None
        
        return banner
    
    def get_second_next_banner(self):
        banners = core_models.Banner.objects.extra(where=["%s >= fecha_publicacion"],
            params=[hoy]).filter(Q(impresiones_restantes__isnull=True) |
            Q(impresiones_restantes__gt=0)).filter(estado=core_mixins.get_active_status()).order_by('?')
        
        if banners.count() > 0:
            print 'get_second_next_banner - Banners', banners.count()
            banner = banners[0]
            """
            if banner.pk == first_banner.pk:
                print 'get_second_next_banner - El banner primero es igual, intentando con el segundo', banner.pk 
                if banners.count() > 1:
                    #print 'get_second_next_banner - El banner segundo es', banners[1].pk
                    banner = banners[1]
                    
                else:
                    #print 'El banner segundo no existe'
                    return None
            else:
                print 'get_second_next_banner - El banner segundo es distinto'
            """
            if banner.impresiones_restantes is None:
                print 'Error - El banner mostrado no tiene impresiones'
                if banner.impresiones:
                    banner.impresiones_restantes = banner.impresiones
                else:
                    banner.impresiones_restantes = 1
            banner.impresiones_restantes -= 1
            banner.save()
        else:
            banner = None
        
        return banner
        
    def get_banners_query(self):
        queries = [Q(ruc_empresa=self.get_identificacion_usuario())]
        try:
            self.cleaned_data = self.form.cleaned_data.copy()
            self.get_dates_query(queries, 'ban_fecha_inicio', 'ban_fecha_fin')            
            if self.cleaned_data['ban_nombre']: queries += [Q(nombre__icontains=self.cleaned_data['ban_nombre'])]
            if self.cleaned_data['ban_estado']: queries += [Q(estado=self.cleaned_data['ban_estado'])]
            self.filas = self.cleaned_data['ban_filas_banner']
        except Exception as e:
            print 'get_banners_query - Error:', e
        return self.build_query(queries)
    
    def process(self):
        query = self.get_banners_query()
        banners = []
        if query:
            banners = core_models.Banner.objects.filter(query).order_by('-fecha_creacion')
            self.cantidad = banners.count()
        
        return self.paginar(banners)
        
class FiltroBannerAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
        
    def process_filter(self, form):
        try:
            form = er_forms.FormFiltroBanner(deserialize_form(form))
            if form.is_valid():
                helper = FiltroBannerHelper(self.request, form)
                banners = helper.process()
                if banners:
                    html = render_to_string('webparts/banners/banners_list_items.html', {'banners_empresa': banners})
                    self.dajax.assign('#banners_items', 'innerHTML', html)
                    self.dajax.assign('#cantidad-banners', 'innerHTML', str(helper.cantidad))
                else:
                    self.dajax.assign('#banners_items', 'innerHTML', '')
                    self.dajax.assign('#cantidad-banners', 'innerHTML', '0')
                    self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'No se encontraron resultados')
            else:
                print form.errors
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))

        return self.return_ajax(self.dajax)

class ClientesHelper(object):
    
    def get_empresas_cliente(self, identificacion_cliente):
        # TODO: Poner cache
        empresas = list(core_models.Documento.objects.filter(identificacion_receptor = identificacion_cliente).values('ruc_emisor').order_by('-fecha_emision'))
        empresas += list(core_models.BuzDocumento.objects.filter(buzon__identificacion = identificacion_cliente).values('ruc_emisor').order_by('-fecha_emision'))
        return [e['ruc_emisor'] for e in empresas]
    
clientes_helper = ClientesHelper()

class FiltroCuponHelper(FiltroHelper):

    def __init__(self, request=None, form=None):
        self.request = request
        self.form = form
        self.filas = 5
        self.cantidad = 0
        self.page_name = 'page_cupon'
        
    def get_cupones_query(self, is_public=True):
        if is_public:
            # TODO: Cupones solo de la empresa donde se es cliente
            queries = [Q(ruc_empresa__in=clientes_helper.get_empresas_cliente(self.get_identificacion_usuario()))]
        else:
            queries = [Q(ruc_empresa=self.get_identificacion_usuario())]
        try:
            self.cleaned_data = self.form.cleaned_data.copy()
            self.get_publish_dates_query(queries, 'cup_fecha_inicio', 'cup_fecha_fin')   
            if self.cleaned_data['cup_tipo']: queries += [Q(tipo_cupon=self.cleaned_data['cup_tipo'])]
            if self.cleaned_data['cup_estado']: queries += [Q(estado=self.cleaned_data['cup_estado'])]
            if self.cleaned_data['cup_categoria']: queries += [Q(categoria=self.cleaned_data['cup_categoria'])]
            if self.cleaned_data['cup_sub_categoria']: queries += [Q(sub_categoria=self.cleaned_data['cup_sub_categoria'])]
            self.filas = self.cleaned_data['cup_filas_cupones']
        except Exception as e:
            print 'get_cupones_query - Error:', e
        return self.build_query(queries)
    
    def process(self, is_public=True):
        query = self.get_cupones_query(is_public)
        cupones = []
        if query:
            if is_public:
                cupones = core_models.Cupon.objects.filter(query).extra(where=["%s >= fecha_publicacion AND %s <= fecha_final_publicacion"],
                                    params=[hoy, hoy]).filter(estado=core_mixins.get_active_status()).order_by('-fecha_publicacion')
            else:
                cupones = core_models.Cupon.objects.filter(query).order_by('-fecha_creacion')
            self.cantidad = cupones.count()
        
        return self.paginar(cupones)
    
class FiltroCuponAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
        
    def get_is_public(self):
        try:
            perfil_usuario = self.request.user.get_profile()
            if perfil_usuario.ruc_empresa is not None:
                return False
        except:
            pass
        return True        
        
    def process_filter(self, form):
        try:
            form = er_forms.FormFiltroCupon(deserialize_form(form))
            if form.is_valid():
                helper = FiltroCuponHelper(self.request, form)
                cupones = helper.process(self.get_is_public())
                if cupones:
                    html = render_to_string('webparts/cupones/cupones_list_items.html', {'cupones_empresa': cupones,
                                                                                         'DOMAIN_INNOBEE':settings.DOMAIN_INNOBEE,
                                                                                         'STATIC_URL':settings.STATIC_URL})
                    self.dajax.assign('#cupones_list', 'innerHTML', html)
                    self.dajax.assign('#cantidad-cupones', 'innerHTML', str(helper.cantidad))
                else:
                    self.dajax.assign('#cupones_list', 'innerHTML', '')
                    self.dajax.assign('#cantidad-cupones', 'innerHTML', '0')
                    self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'No se encontraron resultados')
            else:
                print form.errors
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))

        return self.return_ajax(self.dajax)
    
class FiltroProductoHelper(FiltroHelper):

    def __init__(self, request=None, form=None):
        self.request = request
        self.form = form
        self.filas = 5
        self.cantidad = 0
        self.page_name = 'page_produc'
        
    def get_productos_query(self, is_public=True):
        if is_public:
            # TODO: Productos solo de la empresa donde se es cliente
            queries = [Q(estado=core_mixins.get_active_status())]#[Q(ruc_empresa__in=clientes_helper.get_empresas_cliente(self.get_identificacion_usuario()))]
        else:
            queries = [Q(ruc_empresa=self.get_identificacion_usuario())]
        try:
            self.cleaned_data = self.form.cleaned_data.copy()
            self.get_publish_dates_query(queries, 'pro_fecha_inicio', 'pro_fecha_fin')
            if self.cleaned_data['pro_nombre_producto']: queries += [Q(titulo__icontains=self.cleaned_data['pro_nombre_producto'])]
            if self.cleaned_data['pro_codigo']: queries += [Q(codigo_sku=self.cleaned_data['pro_codigo'])]
            if self.cleaned_data['pro_estado']: queries += [Q(estado=self.cleaned_data['pro_estado'])]
            if self.cleaned_data['pro_categoria']: queries += [Q(categoria=self.cleaned_data['pro_categoria'])]
            if self.cleaned_data['pro_sub_categoria']: queries += [Q(sub_categoria=self.cleaned_data['pro_sub_categoria'])]
            self.filas = self.cleaned_data['pro_filas_producto']
        except Exception as e:
            print 'get_productos_query - Error:', e
        return self.build_query(queries)
    
    def process(self, is_public=True):
        query = self.get_productos_query(is_public)
        #print 'queries productos {0}'.format(query), 'public', is_public
        productos = []
        if query:
            if is_public:
                productos = core_models.Producto.objects.filter(query).extra(where=["%s >= fecha_publicacion"],
                                    params=[hoy]).order_by('-fecha_publicacion')
            else:
                productos = core_models.Producto.objects.filter(query).order_by('-fecha_creacion')
            self.cantidad = productos.count()
        
        return self.paginar(productos)
    
class FiltroProductoAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
        
    def get_is_public(self):
        try:
            perfil_usuario = self.request.user.get_profile()
            if perfil_usuario.ruc_empresa is not None:
                return False
        except:
            pass
        return True
        
    def process_filter(self, form):
        try:
            form = er_forms.FormFiltroProducto(deserialize_form(form))
            if form.is_valid():
                helper = FiltroProductoHelper(self.request, form)
                productos = helper.process(self.get_is_public())
                if productos:
                    html = render_to_string('webparts/productos/productos_list_items.html', {'productos_interes': productos,
                                                                                         'DOMAIN_INNOBEE':settings.DOMAIN_INNOBEE,
                                                                                         'STATIC_URL':settings.STATIC_URL})
                    self.dajax.assign('#productos_list', 'innerHTML', html)
                    self.dajax.assign('#cantidad-productos', 'innerHTML', str(helper.cantidad))
                else:
                    self.dajax.assign('#productos_list', 'innerHTML', '')
                    self.dajax.assign('#cantidad-productos', 'innerHTML', '0')
                    self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'No se encontraron resultados')
            else:
                print form.errors
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))

        return self.return_ajax(self.dajax)
        
class FiltroCampaniasHelper(FiltroHelper):

    def __init__(self, request=None, form=None, page_name='page_camp'):
        self.request = request
        self.form = form
        self.filas = 5
        self.cantidad = 0
        self.page_name = page_name
        self.cleaned_data = None
        
    def get_campanias_query(self):
        queries = [Q(ruc_empresa=self.get_identificacion_usuario())]
        try:
            self.cleaned_data = self.form.cleaned_data.copy()
            self.get_cdates_query(queries, 'cam_fecha_inicio', 'cam_fecha_fin')
            if self.cleaned_data['cam_nombre']: queries += [Q(titulo__icontains=self.cleaned_data['cam_nombre'])]
            if self.cleaned_data['cam_estado']: queries += [Q(estado=self.cleaned_data['cam_estado'])]
            self.filas = self.cleaned_data['cam_filas_campanias']
        except Exception as e:
            print 'get_campanias_query - Error:', e
        return self.build_query(queries)
    
    def process(self):
        query = self.get_campanias_query()
        campanias_sms, campanias_email = [], []
        if query:
            if self.cleaned_data and self.cleaned_data['cam_tipo']:
                if self.cleaned_data['cam_tipo'] == 'sms':
                    campanias_sms = core_models.CampaniaSms.objects.extra(select={'tipo_campania': "'sms'"}).\
                        values('id_campania_sms','ruc_empresa','nombre','fecha_publicacion','mensaje', 'fecha_creacion','estado').\
                        filter(query).order_by('-fecha_creacion')
                else:
                    campanias_email = core_models.CampaniaEmail.objects.extra(select={'tipo_campania': "'email'"}).\
                        values('id_campania','ruc_empresa','nombre','fecha_publicacion','subject_email',
                               'banner_superior','url_apunta_banner_superior','texto','fecha_creacion','estado').\
                                filter(query).order_by('-fecha_creacion')
            else:
                campanias_email = core_models.CampaniaEmail.objects.extra(select={'tipo_campania': "'email'"}).\
                    values('id_campania','ruc_empresa','nombre','fecha_publicacion','subject_email',
                           'banner_superior','url_apunta_banner_superior','texto','fecha_creacion','estado').\
                            filter(query).order_by('-fecha_creacion')
            
                campanias_sms = core_models.CampaniaSms.objects.extra(select={'tipo_campania': "'sms'"}).\
                    values('id_campania_sms','ruc_empresa','nombre','fecha_publicacion','mensaje', 'fecha_creacion','estado').\
                            filter(query).order_by('-fecha_creacion')
                
            resultado_campania = list(chain(campanias_email, campanias_sms))            
            self.cantidad = len(resultado_campania)
        
        return self.paginar(resultado_campania)
    
    def process_sms(self):
        query = self.get_campanias_query()
        campanias_sms = []
        if query:
            campanias_sms = core_models.CampaniaSms.objects.filter(query).order_by('-fecha_creacion')
            self.cantidad = len(campanias_sms)
            print 'ENCONTRADOS SMS', self.cantidad
        return self.paginar(campanias_sms)
    
    def process_email(self):
        query = self.get_campanias_query()
        campanias_email = []
        if query:
            print 'queries email {0}'.format(query)
            campanias_email = core_models.CampaniaEmail.objects.filter(query).order_by('-fecha_creacion')
            self.cantidad = len(campanias_email)
            print 'ENCONTRADOS EMAILS', self.cantidad
        return self.paginar(campanias_email)

class FiltroCampaniasAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
            
    def process_filter(self, form):
        try:
            form = er_forms.FormFiltroCampanias(deserialize_form(form))
            if form.is_valid():
                helper = FiltroCampaniasHelper(self.request, form)
                campanias = helper.process()
                if campanias:
                    html = render_to_string('webparts/campanias/campanias_list_items.html', {'resultado_campania': campanias})
                    self.dajax.assign('#campanias_list', 'innerHTML', html)
                    self.dajax.assign('#cantidad-campanias', 'innerHTML', str(helper.cantidad))
                else:
                    self.dajax.assign('#campanias_list', 'innerHTML', '')
                    self.dajax.assign('#cantidad-campanias', 'innerHTML', '0')
                    self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'No se encontraron resultados')
            else:
                print form.errors
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))

        return self.return_ajax(self.dajax)
    
    def process_filter_sms(self, form):
        try:
            form = er_forms.FormFiltroCampanias(deserialize_form(form))
            if form.is_valid():
                helper = FiltroCampaniasHelper(self.request, form, page_name='page_sms')
                campanias = helper.process_sms()
                if campanias:
                    html = render_to_string('webparts/campanias/campanias_sms_list_items.html', {'campania_sms': campanias})
                    self.dajax.assign('#campanias_sms_list', 'innerHTML', html)
                    self.dajax.assign('#cantidad-campanias_sms', 'innerHTML', str(helper.cantidad))
                else:
                    self.dajax.assign('#campanias_sms_list', 'innerHTML', '')
                    self.dajax.assign('#cantidad-campanias_sms', 'innerHTML', '0')
                    self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'No se encontraron resultados')
            else:
                print form.errors
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))

        return self.return_ajax(self.dajax)
    
    def process_filter_email(self, form):
        from innobee_util.mail_chimp import reporte_campania
        try:
            form = er_forms.FormFiltroCampanias(deserialize_form(form))
            if form.is_valid():
                helper = FiltroCampaniasHelper(self.request, form, page_name='page_email')
                campanias = helper.process_email()
                if campanias:
                    fecha_actual_gmt = datetime.datetime.now()        
                    for item in campanias:
                        reporte = reporte_campania(item.id_campania)
                        if reporte:
                            item.opens = reporte['opens']
                            item.clicks = reporte['clicks']
                            item.nro_enviados = reporte['emails_sent']
                        else:
                            item.opens = 0
                            item.clicks = 0
                            item.nro_enviados = 0
                        if item.fecha_publicacion > fecha_actual_gmt:
                            item.editable = True
                        else:
                            item.editable = False
                    
                    html = render_to_string('webparts/campanias/campanias_email_list_items.html', {'campania_email': campanias})
                    self.dajax.assign('#campanias_email_list', 'innerHTML', html)
                    self.dajax.assign('#cantidad-campanias_email', 'innerHTML', str(helper.cantidad))
                else:
                    self.dajax.assign('#campanias_email_list', 'innerHTML', '')
                    self.dajax.assign('#cantidad-campanias_email', 'innerHTML', '0')
                    self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'No se encontraron resultados')
            else:
                print form.errors
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))

        return self.return_ajax(self.dajax)
    
class FiltroReportesHelper(FiltroHelper):

    def __init__(self, request=None, form=None):
        self.request = request
        self.form = form
        self.filas = -1
        self.cantidad = 0
        self.page_name = None
        self.fecha_desde = '---'
        self.fecha_hasta = '---'
        
    def get_reporte_query(self, identificacion_emisor, fuente_generacion=None):
        queries = [Q(estado=core_mixins.get_active_status())]
            
        if identificacion_emisor:
            queries += [Q(ruc_emisor=identificacion_emisor) & Q(estado_notificacion=core_mixins.get_authorized_notif_status())]
                
        if fuente_generacion:
            queries += [Q(fuente_generacion=fuente_generacion)]

        try:
            self.cleaned_data = self.form.cleaned_data.copy()
            self.fecha_desde, self.fecha_hasta = self.cleaned_data['fecha_inicio'], self.cleaned_data['fecha_fin']
            if self.fecha_desde and self.fecha_hasta: queries += [Q(fecha_emision__range = (self.fecha_desde,self.fecha_hasta))]
            elif self.fecha_desde and not self.fecha_hasta: queries += [Q(fecha_emision__gte=self.fecha_desde)]
            elif self.fecha_hasta and not self.fecha_desde: queries += [Q(fecha_emision__lte=self.fecha_hasta)]
            if self.cleaned_data['tipo_comprobante']: queries += [Q(tipo_comprobante=self.cleaned_data['tipo_comprobante'])]
            if 'identificacion' in self.cleaned_data and self.cleaned_data['identificacion']:
                queries += [Q(identificacion_receptor=self.cleaned_data['identificacion'])]
                
            if not self.fecha_desde: self.fecha_desde = '---'
            if not self.fecha_hasta: self.fecha_hasta = '---'
        except Exception as e:
            print 'get_productos_query - Error:', e
        return self.build_query(queries)
    
    def process(self, identificacion_emisor, separated_sources=False):
        if not separated_sources:
            query = self.get_reporte_query(identificacion_emisor)
            query2 = None
        else:
            query = self.get_reporte_query(identificacion_emisor, P.ORIGEN_INNOBEE)
            query2 = self.get_reporte_query(identificacion_emisor, P.ORIGEN_BUZON)
        
        print 'query 1 {0}'.format(query)
        if query2:
            print 'query 2 {0}'.format(query2)
        
        documentos = core_models.Documento.objects.filter(query)
        
        if not separated_sources:
            suma_comprobantes = documentos.aggregate(Sum('monto_total'))
            return suma_comprobantes['monto_total__sum'] or 0
        else:
            print 'Documentos A', documentos.count()
            suma_comprobantes1 = documentos.aggregate(Sum('monto_total'))
            documentos2 = core_models.Documento.objects.filter(query2)
            print 'Documentos B', documentos2.count()
            suma_comprobantes2 = documentos2.aggregate(Sum('monto_total'))
            if documentos.count() > 0:
                razon_social_receptor = documentos[0].razon_social_receptor
            elif documentos2.count() > 0:
                razon_social_receptor = documentos2[0].razon_social_receptor
            else:
                razon_social_receptor =  '---'
            return suma_comprobantes1['monto_total__sum'] or 0, suma_comprobantes2['monto_total__sum'] or 0, razon_social_receptor
    
class FiltroReportesAjaxHelper(FiltroAjaxHelper):
    
    def __init__(self, request):
        self.dajax = Dajax()
        self.request = request
        
    def process_filter_general(self, form):
        try:
            form = er_forms.FrmFiltroRepGen(deserialize_form(form))
            if form.is_valid():
                helper = FiltroReportesHelper(self.request, form)
                suma = helper.process(self.get_ruc_empresa())
                if suma:
                    html = render_to_string('webparts/reportes/reporte_general_item.html', {'suma_facturas': suma})
                    self.dajax.assign('#reporte_general_content', 'innerHTML', html)
                else:
                    self.dajax.assign('#reporte_general_content', 'innerHTML', 'No se encontraron resultados con esos terminos de busqueda')
            else:
                print form.errors
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))

        return self.return_ajax(self.dajax)
    
    def process_filter_individual(self, form):
        try:
            form = er_forms.FrmFiltroRepInv(deserialize_form(form))
            if form.is_valid():
                helper = FiltroReportesHelper(self.request, form)
                suma1, suma2, razon_social_receptor = helper.process(self.get_ruc_empresa(), True)
                if (suma1 or suma2) and razon_social_receptor:
                    suma_facturas_receptor = suma1 + suma2
                    print 'DATES', helper.fecha_desde, helper.fecha_hasta
                    html = render_to_string('webparts/reportes/reporte_individual_item.html', {'suma_facturas_innobee': suma1,
                                                                                          'suma_facturas_buzon':suma2,
                                                                                          'razon_social_receptor':razon_social_receptor,
                                                                                          'suma_facturas_receptor':suma_facturas_receptor,
                                                                                          'fecha_inicio':helper.fecha_desde,
                                                                                          'fecha_fin':helper.fecha_hasta })
                    self.dajax.assign('#reporte_individual_content', 'innerHTML', html)

                else:
                    self.dajax.assign('#reporte_individual_content', 'innerHTML', 'No se encontraron resultados con esos terminos de busqueda')
            else:
                self.dajax.alert('La IDENTIFICACION es requerida')
        except Exception as e:
            traceback.print_exc()
            self.dajax.assign('#pleaseWaitDialog-alert', 'innerHTML', 'Error: %s' % str(e))

        return self.return_ajax(self.dajax)
    
    
def cambiar_estado_comprobante_emitido(username, tipo_comprobante, comprobante_id, codigo_anulacion, code_is_original_code=False):
    estado = None
    if code_is_original_code:
        docs = core_models.Documento.objects.filter(codigo_original=comprobante_id, tipo_comprobante=tipo_comprobante)
    else:
        docs = core_models.Documento.objects.filter(pk=comprobante_id, tipo_comprobante=tipo_comprobante)

    for doc in docs:
        if doc.estado == core_mixins.get_active_status():
            print 'Anulando comprobante', doc.codigo_original 
            doc.estado = core_mixins.get_anulado_status()
        elif doc.estado == core_mixins.get_anulado_status():
            print 'Activando comprobante', doc.codigo_original
            doc.estado = core_mixins.get_active_status()
        if doc.estado.nombre_estado: estado = doc.estado.nombre_estado
        estado = doc.estado
        if codigo_anulacion != '0':
                doc.codigo_anulacion = codigo_anulacion
        doc.usuario_actualizacion = username
        doc.fecha_actualizacion = datetime.datetime.now()
        doc.save()
    return estado

def renotificar_comprobante_emitido(username, tipo_comprobante, comprobante_id, emails_notificacion):
    docs = core_models.Documento.objects.filter(id=comprobante_id, tipo_comprobante=tipo_comprobante)
    if len(docs) > 0:
        empresa = core_models.PorEmpresa.objects.get(ruc = docs[0].ruc_emisor)
        if empresa:
            print 'Encontrados docs', tipo_comprobante, '-', comprobante_id, ':', docs
            doc = docs[0]
            if util.enviar_email_notificacion(emails_notificacion, doc, empresa):
                print 'Re-NOTIFICANDO', doc.codigo_original
                doc.fecha_actualizacion = datetime.datetime.now()
                doc.save()
                return True
    return False

class ReporteEmpresa(object):
    
    def __init__(self, empresa):
        self.empresa = empresa

    def procesar(self, mes, anio):
        documentos_emitidos = core_models.Documento.objects.filter(ruc_emisor = self.empresa.ruc,
                fecha_creacion__month=mes, fecha_creacion__year=anio).exclude(estado=core_mixins.get_inactive_status())

        documentos_recibidos = core_models.Documento.objects.filter(identificacion_receptor = self.empresa.ruc,
                fecha_creacion__month=mes, fecha_creacion__year=anio).exclude(estado=core_mixins.get_inactive_status())

        documentos_emitidos_annotate = documentos_emitidos.values('tipo_comprobante').annotate(Count('tipo_comprobante'),Sum('monto_total'))
        documentos_recibidos_anotate = documentos_recibidos.values('tipo_comprobante').annotate(Count('tipo_comprobante'),Sum('monto_total'))

        return ObjetoReporte(self.empresa, documentos_emitidos_annotate, documentos_recibidos_anotate)

class ObjetoReporte(object):

    def __init__(self, empresa, emitidos, recibidos):
        self.empresa = empresa
        self.emitidos = emitidos
        self.recibidos = recibidos
        self.total_emitidos = 0
        self.monto_total_emitido = 0
        self.total_recibidos = 0
        self.monto_total_recibido = 0
        self.sumar()

    def sumar(self):
        for doc_rec in self.emitidos:
            self.total_emitidos += float(doc_rec['tipo_comprobante__count'])
            self.monto_total_emitido = float(doc_rec['monto_total__sum'])

        for doc_rec in self.recibidos:
            self.total_recibidos += float(doc_rec['tipo_comprobante__count'])
            self.monto_total_recibido = float(doc_rec['monto_total__sum'])

class ReporteInnobee(object):

    def __init__(self, request, form):
        if form is None:
            self.mes = request.session['reporte-mes']
            self.anio = request.session['reporte-anio']
        else:
            try :
                self.cleaned_data = form.cleaned_data.copy()
                self.mes = self.cleaned_data['mes']
                self.anio = self.cleaned_data['anio']
            except:
                ahora = datetime.datetime.now()
                self.mes = ahora.month
                self.anio = ahora.year

            request.session['reporte-mes'] = self.mes
            request.session['reporte-anio'] = self.anio

        self.total_emitido = 0
        self.monto_total_emitido = 0
        self.total_recibido = 0
        self.monto_total_recibido = 0

    def procesar(self):
        lista = []
        empresas = core_models.PorEmpresa.objects.filter(estado=core_mixins.get_active_status())

        for empresa in empresas:
            reporte = ReporteEmpresa(empresa)
            obj = reporte.procesar(self.mes, self.anio)
            lista.append(obj)
            self.total_emitido +=  obj.total_emitidos
            self.monto_total_emitido +=  obj.monto_total_emitido
            self.total_recibido +=  obj.total_recibidos
            self.monto_total_recibido +=  obj.monto_total_recibido
        return lista

