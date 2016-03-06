# Create your views here.
# -*- encoding: utf-8 -*-
import json
import datetime
from types import NoneType
import sys

from django.views.generic import ListView, CreateView, UpdateView
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, F
from django.http import HttpResponse, HttpResponseRedirect
from visits.models import Visit
from django.contrib import messages

from django.http import Http404
from django.template.loader import render_to_string

import xlwt
import traceback

from core.models import Documento, PorEmpresa, \
    PorOperador, BuzDocumento, PorSubcategoria, \
    Cupon, Producto, Banner, CampaniaEmail, CampaniaSms, BuzBuzon, PorEstado, \
    PorFuenteRecepcion

from emisor_receptor.forms import FiltroDocumento, FiltroDocumentoRecibidos, \
    FormComprobantesCargados, \
    BuzDocForm, CuponFormulario, BannerForm, CampaniaEmailForm, \
    CampaniaSMSForm, ProductoForm, FormFiltroCupon, FormFiltroProducto, \
    FormFiltroCampanias, PorOperadorForm, FrmFiltroRepGen, FrmFiltroRepInv, \
    PorEmpresaForm, PorOperadorIncompleteForm, FrmFiltroRepInnobee

from adm import helpers
# variables globales utilizadas para exportar a xls
from innobee_util.util import LoggedInMixin, add_log_error
from emisor_receptor import decorators
from emisor_receptor import helpers as er_helpers

#from core import mixins as core_mixins
from core import helper as core_helpers
from django.db import connections
from django.http import HttpResponse

documentos_recib = ''
documentos_emit = ''
result_campanias = ''


def filtrar_documentos_cargados(frm_filtro_documento):
    queries = []
    if frm_filtro_documento.cleaned_data['fecha']:
        queries += [Q(fecha_emision=frm_filtro_documento.cleaned_data['fecha'])]
    if frm_filtro_documento.cleaned_data['tipo_comprobante']:
        queries += [Q(tipo_comprobante=frm_filtro_documento.cleaned_data['tipo_comprobante'])
        ]
    if frm_filtro_documento.cleaned_data['numero']:
        queries += [Q(numero_comprobante=frm_filtro_documento.cleaned_data['numero'])
        ]
    if frm_filtro_documento.cleaned_data['emisor']:
        queries += [Q(razon_social_emisor__icontains=frm_filtro_documento.cleaned_data['emisor']) |
                    Q(ruc_emisor=frm_filtro_documento.cleaned_data['emisor'])]
    return queries


def filtro_rep_gen(frm_rep_gen):
    queries = []

    fecha_inicio = frm_rep_gen.cleaned_data['fecha_inicio']
    fecha_fin = frm_rep_gen.cleaned_data['fecha_fin']
    # cedula = frm_rep_gen.cleaned_data['cedula']

    if fecha_inicio and fecha_fin:
        queries += [Q(fecha_creacion__range=(fecha_inicio, fecha_fin))]
    elif fecha_inicio and not fecha_fin:
        queries += [
            Q(fecha_creacion=frm_rep_gen.cleaned_data['fecha_inicio'])
        ]
    # if frm_rep_gen.cleaned_data['cedula']:
    # queries += [Q(identificacion_receptor=frm_rep_gen.cleaned_data['cedula'])]

    return queries


def filtro_rep_ind(frm_rep_gen):
    queries = []

    fecha_inicio = frm_rep_gen.cleaned_data['fecha_inicio']
    fecha_fin = frm_rep_gen.cleaned_data['fecha_fin']
    cedula = frm_rep_gen.cleaned_data['cedula']

    if fecha_inicio and fecha_fin:
        queries += [Q(fecha_creacion__range=(fecha_inicio, fecha_fin))]
    elif fecha_inicio and not fecha_fin:
        queries += [
            Q(fecha_creacion=frm_rep_gen.cleaned_data['fecha_inicio'])
        ]
    if cedula:
        queries += [Q(identificacion_receptor=cedula)]

    return queries


def filtro_rep_glob(frm_rep_glob):
    queries = []

    fecha_inicio = frm_rep_glob.cleaned_data['fecha_inicio']
    fecha_fin = frm_rep_glob.cleaned_data['fecha_fin']

    if frm_rep_glob and fecha_fin:
        queries += [Q(fecha_creacion__range=(fecha_inicio, fecha_fin))]
    elif fecha_inicio and not fecha_fin:
        queries += [
            Q(fecha_creacion=frm_rep_glob.cleaned_data['fecha_inicio'])
        ]
    if frm_rep_glob.cleaned_data['categoria']:
        queries += [
            Q(fuente_recepcion=frm_rep_glob.cleaned_data['fuente'])
        ]

    return queries


def get_identificacion_usuario(request):
    identificacion = None
    try:
        perfil_usuario = request.user.get_profile()
    
        if perfil_usuario.ruc_empresa is not None:
            identificacion = perfil_usuario.ruc_empresa
        else:
            identificacion = perfil_usuario.identificacion
    except:
        pass
    return identificacion


hoy = datetime.datetime.now()
hoy = hoy.strftime('%Y-%m-%d')

#queries_recibidos_aux_dashboard = [Q()]
#queries_emitidos_aux_dashboard = [Q()]
#queries_cargados_aux_dashboard = [Q()]
#queries_cupon_aux_dashboard = [Q()]
#queries_productos_aux_dashboard = [Q()]
#queries_campanias_aux_dashboard = [Q()]


from django.core.paginator import Paginator, InvalidPage, EmptyPage

def get_pagination_page(request, page_name, items, filas, page=1):
    request.session[page_name] = str(page)
    paginator = Paginator(items, filas)
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    try:
        items = paginator.page(page)
    except (EmptyPage, InvalidPage):
        items = paginator.page(paginator.num_pages)
    return items

@login_required
@decorators.profile_required
def inicio(request):
    "Funcion que muestra la pagina inicial de los usuarios receptores"
    template = "emisores/inicio.html"
    
    print 'INICIO', request.user
    
    buzon_redirect = helpers.BuzonRedirectHelper(request.user)
    if buzon_redirect.has_profile():
        if not buzon_redirect.verificar_buzon_completo():
            return buzon_redirect.redirigir()
    else:
        operador_por_crear = helpers.PorOperadorPorCrearHelper(request.user.username, request.user.password)
        operador_por_crear.create_if_not_exist()

    if core_helpers.check_user_has_incomplete_information(request.user):
        return HttpResponseRedirect('/update-profile')
    
    empresa_usuario = ''
    
    try:
        perfil_usuario = request.user.get_profile()
        if perfil_usuario.ruc_empresa is not None:
            empresa_usuario = PorEmpresa.objects.get(ruc=perfil_usuario.ruc_empresa)
    except:
        pass

    ban_helper = er_helpers.FiltroBannerHelper()
    banner = ban_helper.get_next_banner()
    banner_secondary = ban_helper.get_second_next_banner() #ban_helper.get_second_next_banner(banner)

    # --------------------------
    
    # DOCUMENTOS EMITIDOS - INICIO
    if request.POST:
        frm_filtro_emit = FiltroDocumento(request.POST)
        frm_filtro_emit.is_valid()
    else:
        frm_filtro_emit = FiltroDocumento()
        
    doc_emit_helper = er_helpers.FiltroDocumentoHelper(request, frm_filtro_emit, 'emitidos')
    documentos_emitidos = doc_emit_helper.process()
    # DOCUMENTOS EMITIDOS - FIN
    
    # DOCUMENTOS RECIBIDOS - INICIO
    if request.POST:
        frm_filtro_recibido = FiltroDocumentoRecibidos(request.POST)
        frm_filtro_recibido.is_valid()
    else:
        frm_filtro_recibido = FiltroDocumentoRecibidos()
        
    doc_recib_helper = er_helpers.FiltroDocumentoHelper(request, frm_filtro_recibido, 'recibidos')
    documentos_recibidos = doc_recib_helper.process()
    # DOCUMENTOS RECIBIDOS - FIN
    
    # DOCUMENTOS CARGADOS - INICIO
    if request.POST:
        frm_filtro_doc_carg = FormComprobantesCargados(request.POST)
        frm_filtro_doc_carg.is_valid()
    else:
        frm_filtro_doc_carg = FormComprobantesCargados()
        
    doc_carg_helper = er_helpers.FiltroDocumentoHelper(request, frm_filtro_doc_carg, 'cargados')
    documentos_cargados = doc_carg_helper.process()
    # DOCUMENTOS CARGADOS - FIN
    
    # CUPONES - INICIO
    if request.POST:
        frm_filtro_cupon = FormFiltroCupon(request.POST)
        frm_filtro_cupon.is_valid()
    else:
        frm_filtro_cupon = FormFiltroCupon()
        
    cupon_helper = er_helpers.FiltroCuponHelper(request, frm_filtro_cupon)
    cupones_empresa = cupon_helper.process()
    # CUPONES - FIN
    
    # PRODUCTOS - INICIO
    if request.POST:
        frm_filtro_productos = FormFiltroProducto(request.POST)
        frm_filtro_productos.is_valid()
    else:
        frm_filtro_productos = FormFiltroProducto()
        
    prod_helper = er_helpers.FiltroProductoHelper(request, frm_filtro_productos)
    productos_interes = prod_helper.process()
    # PRODUCTOS - FIN
    
    # CAMPANIAS - INICIO
    if request.POST:
        frm_filtro_campanias = FormFiltroCampanias(request.POST)
        frm_filtro_campanias.is_valid()
    else:
        frm_filtro_campanias = FormFiltroCampanias()
        
    camp_helper = er_helpers.FiltroCampaniasHelper(request, frm_filtro_campanias)
    resultado_campania = camp_helper.process()
    # CAMPANIAS - FIN
    # --------------------------
    
    suma_documentos_emitidos = 0
    if doc_emit_helper: suma_documentos_emitidos = doc_emit_helper.suma_documentos
      
    suma_documentos_recibidos = 0
    if doc_recib_helper: suma_documentos_recibidos = doc_recib_helper.suma_documentos

    suma_documentos_cargados = 0
    if doc_carg_helper: suma_documentos_cargados = doc_carg_helper.suma_documentos

    cant_doc_rec = 0
    if doc_recib_helper: cant_doc_rec = doc_recib_helper.cantidad
    cant_doc_emit = 0
    if doc_emit_helper: cant_doc_emit = doc_emit_helper.cantidad
    cant_doc_carg = 0
    if doc_carg_helper: cant_doc_carg = doc_carg_helper.cantidad
    cant_cupones = 0
    if cupon_helper: cant_cupones = cupon_helper.cantidad
    cant_productos = 0
    if prod_helper: cant_productos = prod_helper.cantidad
    cant_campanias = 0
    if camp_helper: cant_campanias = camp_helper.cantidad

    context = {'documentos_emitidos': documentos_emitidos,
               'documentos_recibidos': documentos_recibidos,
               'cupones_empresa': cupones_empresa,
               'productos_interes': productos_interes,
               'resultado_campania': resultado_campania,
               'frm_filtro': frm_filtro_emit,
               'frm_filtro_recibido': frm_filtro_recibido,
               'frm_cupon': frm_filtro_cupon,
               'frm_productos': frm_filtro_productos,
               'frm_filtro_campanias': frm_filtro_campanias,
               'banner': banner,
               'banner_secondary':banner_secondary,
               'suma_documentos_emitidos': suma_documentos_emitidos,
               'suma_documentos_recibidos': suma_documentos_recibidos,
               'logotipo_empresa': empresa_usuario,
               'frm_filtro_documento': frm_filtro_doc_carg,
               'documentos_cargados': documentos_cargados,
               'cant_campanias': cant_campanias,
               'cant_cupones': cant_cupones,
               'cant_productos': cant_productos,
               'cant_doc_rec': cant_doc_rec,
               'cant_doc_emit': cant_doc_emit,
               'suma_documentos_cargados': suma_documentos_cargados,
               'cant_doc_carg': cant_doc_carg,
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))

queries_emitidos_aux = [Q()]

@login_required
@permission_required('core.listar_doc_emit', login_url='/')
def comprobantes_emitidos(request):
    "Funcion que muestra la los comprobantes emitidos por el usuario"
    template = "emisores/comp-emitidos.html"

    if request.POST:
        frm_filtro = FiltroDocumento(request.POST)
        frm_filtro.is_valid()
    else:
        frm_filtro = FiltroDocumento()

    helper = er_helpers.FiltroDocumentoHelper(request, frm_filtro, 'emitidos')
    documentos_emitidos = helper.process()

    context = {
        'documentos_emitidos': documentos_emitidos,
        'frm_filtro': frm_filtro,
        'suma_documentos_emitidos': helper.suma_documentos,
        'cant_doc_emit': helper.cantidad,
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))

@login_required
@permission_required('core.listar_comp_cargados', login_url='/')
def comprobantes_cargados(request):
    template = "emisores/comprobantes.html"

    if request.POST:
        frm_filtro_doc_carg = FormComprobantesCargados(request.POST)
        frm_filtro_doc_carg.is_valid()
    else:
        frm_filtro_doc_carg = FormComprobantesCargados()
        
    doc_carg_helper = er_helpers.FiltroDocumentoHelper(request, frm_filtro_doc_carg, 'cargados')
    documentos_cargados = doc_carg_helper.process()
    
    try:
        buzon = BuzBuzon.objects.filter(identificacion=get_identificacion_usuario(request))[:1].get()
    except BuzBuzon.DoesNotExist:
        buzon = None

    context = {
        'documentos_cargados': documentos_cargados,
        'frm_filtro_documento': frm_filtro_doc_carg,
        'buzon': buzon,
        'cantidad_comprobantes': doc_carg_helper.cantidad,
        'suma_documentos_cargados': doc_carg_helper.suma_documentos,
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))


@login_required
@permission_required('core.listar_doc_rec', login_url='/')
def comprobantes_recibidos(request):
    "Funcion que muestra los comprobantes recibidos por el usuario"
    template = "emisores/comp-recibidos.html"
    
    
    if request.POST:
        frm_filtro_recibido = FiltroDocumentoRecibidos(request.POST)
        frm_filtro_recibido.is_valid()
    else:
        frm_filtro_recibido = FiltroDocumentoRecibidos()

    helper = er_helpers.FiltroDocumentoHelper(request, frm_filtro_recibido, 'recibidos')
    documentos_recibidos = helper.process()
    
    context = {
        'documentos_recibidos': documentos_recibidos,
        'frm_filtro_recibido': frm_filtro_recibido,
        'suma_documentos_recibidos': helper.suma_documentos,
        'cant_doc_rec': helper.cantidad
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))

@login_required
def faqs(request):
    "Funcion que muestra la pagina inicial de los usuarios receptores"
    template = "emisores/faqs.html"
    context = {}
    return render_to_response(template, context,
                              context_instance=RequestContext(request))

perfiles = ''

class EmpresaOperadores(LoggedInMixin, ListView):
    model = PorOperador
    template_name = 'emisores/perfil.html'
    context_object_name = 'perfiles_habilitados'
    paginate_by = 5

    def get_queryset(self):
        perfil_usuario = self.request.user.get_profile()
        perfiles_habilitados = PorOperador.objects.filter(
            ruc_empresa=perfil_usuario.ruc_empresa
        )
        global perfiles
        perfiles = perfiles_habilitados
        return perfiles_habilitados

@login_required
def editar_perfil_persona_emisor(request, cedula):
    template = "emisores/editar-perfil-persona.html"
    se_guardo = False
    identicacion_user = get_identificacion_usuario(request)
    perfil_empresa = PorEmpresa.objects.filter(ruc=identicacion_user)
    if request.POST:
        #instancia = PorOperador.objects.get(identificacion=cedula)
        instancia = PorOperador.objects.filter(identificacion=cedula)[:1].get()
        frm_perfil_persona = PorOperadorForm(request.POST, instance=instancia)
        if frm_perfil_persona.is_valid():
            se_guardo = True
            frm_perfil_persona.save()
            messages.success(request, 'Sus datos fueron actualizados exitosamente')
            return HttpResponseRedirect('/')
        else:
            messages.error(request, 'Hay errores en el formulario')
    else:
        instancia = PorOperador.objects.get(identificacion=cedula)
        frm_perfil_persona = PorOperadorForm(instance=instancia)
    context = {'se_guardo': se_guardo,
               'frm_perfil_persona': frm_perfil_persona,
               'perfil_empresa': perfil_empresa
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))

@login_required
def actualizar_perfil_operador(request):
    template = "emisores/actualizar-perfil-persona.html"
    datos_empresariales = request.user.get_profile().get_datos_empresariales()
    if request.POST:
        if datos_empresariales:
            frm_perfil_persona = PorOperadorIncompleteForm(request.POST, instance=datos_empresariales)
        else:
            frm_perfil_persona = PorOperadorIncompleteForm(request.POST)
        
        if frm_perfil_persona.is_valid():
            datos_empresariales_operador = frm_perfil_persona.save(commit=False)
            datos_empresariales_operador.operador = request.user.get_profile()
            datos_empresariales_operador.save()
            messages.success(request, 'Sus datos empresariales fueron actualizados exitosamente')
            return HttpResponseRedirect('/')
        else:
            print frm_perfil_persona.errors
            messages.error(request, 'Hay errores en el formulario: Todos los campos son requeridos (y al menos una de las redes sociales de su empresa)')
    else:
        if datos_empresariales:
            frm_perfil_persona = PorOperadorIncompleteForm(instance=datos_empresariales)
        else:
            frm_perfil_persona = PorOperadorIncompleteForm()
    context = {'frm_perfil_persona': frm_perfil_persona}

    return render_to_response(template, context, context_instance=RequestContext(request))

@login_required
def perfil_persona(request):
    "Funcion que muestra la edicion de personas"
    template = "emisores/editar-perfil-persona.html"
    se_guardo = False

    perfil_usuario = request.user.get_profile()
    identificacion = perfil_usuario.identificacion

    instancia = PorOperador.objects.filter(identificacion=identificacion)[:1].get()
    if request.POST:
        frm_perfil_persona = PorOperadorForm(request.POST, instance=instancia)
        if frm_perfil_persona.is_valid():
            se_guardo = True
            frm_perfil_persona.save()
            messages.success(request, 'Sus datos fueron actualizados exitosamente')
            return HttpResponseRedirect('/')
        else:
            messages.error(request, 'Hay errores en el formulario')
            for field in frm_perfil_persona:
                if field.errors:
                   frm_perfil_persona.fields[field.name].widget.attrs['class'] = "form-control error-input"
    else:
        frm_perfil_persona = PorOperadorForm(instance=instancia)
    context = {'se_guardo': se_guardo,
               'frm_perfil_persona': frm_perfil_persona,
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))

def cupon_detalle(request, id_cupon):
    template = "emisores/cupon-detalle.html"

    if len(id_cupon) == 15:
        print 'Buscando codigo', id_cupon
        cupon = get_object_or_404(Cupon, codigo=id_cupon)
    else:
        cupon = get_object_or_404(Cupon, pk=id_cupon)
        
    Visit.objects.add_object_visit(request, obj=cupon)
    cupon_visit = Visit.objects.filter(object_id=cupon.pk, object_model='Cupon')[:1].get()
    Cupon.objects.filter(pk=cupon.pk).update(nro_vistos=cupon_visit.visits)
    context = {'cupon': cupon}
    return render_to_response(template, context, context_instance=RequestContext(request))


def producto_detalle(request, id_prod):
    template = "emisores/producto-detalle.html"
    producto = None
    if len(id_prod) == 15:
        print 'Buscando codigo', id_prod
        producto = get_object_or_404(Producto, codigo=id_prod)
    else:
        try:
            producto = get_object_or_404(Producto, pk=id_prod)
        except:
            pass
        
    if producto:
        Visit.objects.add_object_visit(request, obj=producto)
        producto_visit = Visit.objects.filter(object_id=producto.id, object_model='Producto')[:1].get()
        Producto.objects.filter(pk=producto.id).update(nro_vistos=producto_visit.visits)
    context = {'producto': producto}
    return render_to_response(template, context,
                              context_instance=RequestContext(request))


@login_required
@permission_required('core.reportes', login_url='/')
@decorators.enterprise_profile_required
def reportes(request):
    template = "emisores/reportes.html"    
    
    if request.POST:
        form_gen = FrmFiltroRepGen(request.POST)
        form_gen.is_valid()
    else:
        form_gen = FrmFiltroRepGen()
        
    gen_helper = er_helpers.FiltroReportesHelper(request, form_gen)
    suma_gen = gen_helper.process(request.user.get_profile().ruc_empresa)
    
    if request.POST:
        form_ind = FrmFiltroRepInv(request.POST)
        form_ind.is_valid()
    else:
        form_ind = FrmFiltroRepInv()

    ind_helper = er_helpers.FiltroReportesHelper(request, form_gen)
    suma_ind_i, suma_ind_b, razon_social_receptor = gen_helper.process(request.user.get_profile().ruc_empresa, True)

    context = {'frm_filtro_gen': form_gen,
               'frm_filtro_ind': form_ind,
               'suma_facturas': suma_gen,
               'suma_facturas_innobee': suma_ind_i,
               'suma_facturas_buzon': suma_ind_b,
               'razon_social_receptor': razon_social_receptor,
               'suma_facturas_receptor': suma_ind_i + suma_ind_b
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))

@login_required
def soporte(request):
    template = "emisores/soporte.html"
    context = {}
    return render_to_response(template, context,
                              context_instance=RequestContext(request))


@login_required
def ayuda(request):
    template = "emisores/ayuda.html"
    context = {}
    return render_to_response(template, context,
                              context_instance=RequestContext(request))


@login_required
@permission_required('core.editar_perfil_empresa', login_url='/')
def empresa(request):
    template = "emisores/editar-perfil.html"
    perfil = request.user.get_profile()
    if request.POST:
        instancia = PorEmpresa.objects.get(ruc=perfil.ruc_empresa)
        frm_perfil_empresa = PorEmpresaForm(request.POST, request.FILES,
                                            instance=instancia)
        if frm_perfil_empresa.is_valid():
            frm_perfil_empresa.save()
            messages.success(request, 'Los datos de la empresa fueron actualizados exitosamente')
            return redirect('/')
    else:
        instancia = PorEmpresa.objects.filter(ruc=perfil.ruc_empresa)[:1].get()
        frm_perfil_empresa = PorEmpresaForm(instance=instancia)
    context = {'f': frm_perfil_empresa}

    return render_to_response(template, context,
                              context_instance=RequestContext(request))


@login_required
def blog(request):
    "Funcion que muestra la pagina inicial de los usuarios receptores"
    template = "emisores/productos.html"
    context = {}
    return render_to_response(template, context,
                              context_instance=RequestContext(request))


class DocumentoEditView(LoggedInMixin, UpdateView):
    model = BuzDocumento
    form_class = BuzDocForm
    template_name = 'emisores/cargar-comprobantes.html'
    success_url = '/comprobantes-cargados/'

    def get_object(self):
        obj = BuzDocumento.objects.get(id=self.kwargs['id'])
        return obj

class DocumentoCreateView(LoggedInMixin, CreateView):
    model = BuzDocumento
    form_class = BuzDocForm
    template_name = 'emisores/cargar-comprobantes.html'
    success_url = '/comprobantes-cargados/'

    def form_valid(self, form):
        form_doc = form.save(commit=False)
        identificacion_usuario = get_identificacion_usuario(self.request)
        perfil_usuario = self.request.user.get_profile()
        form_doc.buzon = BuzBuzon.objects.filter(identificacion=identificacion_usuario)[:1].get()
        form_doc.fuente_recepcion = PorFuenteRecepcion.objects. filter(pk='PORTAL')[:1].get()
        form_doc.save()
        return super(DocumentoCreateView, self).form_valid(form)

class CuponCreateView(LoggedInMixin, CreateView):
    model = Cupon
    form_class = CuponFormulario
    template_name = 'emisores/crear-nuevo-cupon.html'
    
    def form_valid(self, form):
        try:
            form_cupon = form.save(commit=False)
            identificacion_usuario = get_identificacion_usuario(self.request)
            empresa_obj = PorEmpresa.objects.get(ruc=identificacion_usuario)
            form_cupon.ruc_empresa = empresa_obj
            form_cupon.save(user = self.request.user)
            self.success_url = '/cupones-descuento'
        except Exception as e:
            print 'CuponCreateView - Error', e
        return super(CuponCreateView, self).form_valid(form)

    def form_invalid(self, form):
        for error in form.errors:
            print error
        return super(CuponCreateView, self).form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(CuponCreateView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

class CuponEditView(LoggedInMixin, UpdateView):
    model = Cupon
    form_class = CuponFormulario
    template_name = 'emisores/crear-nuevo-cupon.html'
    success_url = '/cupones-descuento/'

    def get_object(self):
        obj = get_object_or_404(Cupon, pk=self.kwargs['id'], ruc_empresa=get_identificacion_usuario(self.request))
        return obj
    
    def form_invalid(self, form):
        print form.errors
        return super(CuponEditView, self).form_invalid(form)
    
    def get_form_kwargs(self):
        kwargs = super(CuponEditView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

class ProductoCreateView(LoggedInMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'emisores/crear-nuevo-producto.html'
    success_url = '/productos-interes'

    def form_valid(self, form):
        form_producto = form.save(commit=False)
        identificacion_usuario = get_identificacion_usuario(self.request)
        empresa_obj = PorEmpresa.objects.get(ruc=str(identificacion_usuario))
        form_producto.ruc_empresa = empresa_obj
        form_producto.save()
        return super(ProductoCreateView, self).form_valid(form)

    def form_invalid(self, form):
        print form.errors
        return super(ProductoCreateView, self).form_invalid(form)


class ProductoUpdateView(LoggedInMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'emisores/crear-nuevo-producto.html'
    success_url = '/productos-interes'

    def get_object(self):
        obj = get_object_or_404(Producto, pk=self.kwargs['id'], ruc_empresa=get_identificacion_usuario(self.request))
        return obj


def errors_to_json(errors):
    """
    Convert a Form error list to JSON::
    """
    return dict(
            (k, map(unicode, v))
            for (k,v) in errors.iteritems()
        )

class BannerCreateView(LoggedInMixin, CreateView):
    model = Banner
    form_class = BannerForm
    template_name = 'emisores/crear-nuevo-banner.html'
    success_url = '/campania-publicidad'

    def form_valid(self, form):
        form_banner = form.save(commit=False)
        identificacion_usuario = get_identificacion_usuario(self.request)
        empresa_obj = PorEmpresa.objects.get(ruc=str(identificacion_usuario))
        form_banner.ruc_empresa = empresa_obj
        
        from django.core.files.images import get_image_dimensions
        w, h = get_image_dimensions(form_banner.imagen)
        if w/h < 3 or w/h > 10:
            messages.error(self.request, 'Las dimensiones de la imegen cargadas no son proporcionales')
            return redirect('/campania-publicidad/crear-nuevo-banner/')
        else:
            form_banner.save()
            return super(BannerCreateView, self).form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Se encontraron los siguientes errores en el formulario:')
        for error, v in form.errors.items():
            messages.error(self.request, '%s' % str(v[0]))
        return super(BannerCreateView, self).form_invalid(form)

class BannerEditView(LoggedInMixin, UpdateView):
    model = Banner
    form_class = BannerForm
    template_name = 'emisores/crear-nuevo-banner.html'
    success_url = '/campania-publicidad'

    def get_object(self):
        obj = get_object_or_404(Banner, pk=self.kwargs['id'], ruc_empresa=get_identificacion_usuario(self.request))
        return obj

@login_required
@permission_required('core.add_campaniaemail', login_url='/')
def crear_campania_email(request):
    form_campaniaemail = CampaniaEmailForm(request.POST or None, request.FILES or None)

    if form_campaniaemail.is_valid():
        form = form_campaniaemail.save(commit=False)
        identificacion_usuario = get_identificacion_usuario(request)
        empresa_obj = PorEmpresa.objects.get(ruc=str(identificacion_usuario))
        form.ruc_empresa = empresa_obj
        form.save(user = request.user)
        return redirect('/campania-publicidad')
    else:
        print form_campaniaemail.errors

    return render_to_response('emisores/crear-nueva-campana.html',
                              {'form': form_campaniaemail}, context_instance=RequestContext(request))

@login_required
@permission_required('core.add_campaniaemail', login_url='/')
def editar_campania_email(request, id):
    campania = get_object_or_404(CampaniaEmail, pk=id)
    form_campaniaemail = CampaniaEmailForm(request.POST or None, request.FILES or None, instance=campania)
    
    if request.POST:
        if form_campaniaemail.is_valid():
            form = form_campaniaemail.save(commit=False)
            form.save(user = request.user)
            return redirect('/campania-publicidad')
        else:
            print form_campaniaemail.errors

    return render_to_response('emisores/editar-campania-email.html',
                              {'form': form_campaniaemail}, context_instance=RequestContext(request))

@login_required
@permission_required('core.add_campaniaemail', login_url='/')
def editar_campania_sms(request, id):
    campania = get_object_or_404(CampaniaSms, pk=id)
    campania.fecha_publicacion = None

    form_campaniasms = CampaniaSMSForm(request.POST or None,
                                           request.FILES or None,
                                           instance=campania)
    if request.POST:
        if form_campaniasms.is_valid():
            form = form_campaniasms.save(commit=False)
            perfil_usuario = request.user.get_profile()
            empresa_obj = PorEmpresa.objects.get(
                ruc=str(perfil_usuario.ruc_empresa))
            form.ruc_empresa = empresa_obj

            form.save()
            return redirect('/campania-publicidad')
        else:
            print form_campaniasms.errors

    fecha_actual_gmt = datetime.datetime.now()
    fecha_actual_gmt = fecha_actual_gmt.strftime('%Y-%m-%d %H:%M:%S')
    return render_to_response('emisores/editar-campania-sms.html',
                              {'form': form_campaniasms,
                               'fecha_actual': fecha_actual_gmt
                              },
                              context_instance=RequestContext(request))


@login_required
@permission_required('core.add_campaniasms', login_url='/')
def crear_campania_sms(request):
    form_sms = CampaniaSMSForm(request.POST or None, request.FILES or None)

    if form_sms.is_valid():
        obj = form_sms.save(commit=False)
        identificacion_usuario = get_identificacion_usuario(request)
        obj.ruc_empresa = PorEmpresa.objects.get(ruc=str(identificacion_usuario))
        obj.save()
        return redirect('/campania-publicidad')
    else:
        print form_sms.errors

    fecha_actual = datetime.datetime.now()
    fecha_actual = fecha_actual.strftime('%Y-%m-%d %H:%M:%S')

    return render_to_response('emisores/crear-nuevo-sms.html',
                              {'form': form_sms,
                               'fecha_actual': fecha_actual
                              },
                              context_instance=RequestContext(request))


@login_required
def list_sub_categorias(request):
    if request.is_ajax() and request.GET:
        item = str(request.GET.get('categoria'))
        subs = PorSubcategoria.objects.filter(categoria=item)
        my_list = list(subs.values_list('nombre', flat=True))
        json_data = json.dumps(my_list)
    return HttpResponse(json_data, content_type='application/json')


@login_required
def list_sub_categorias_editar(request, id):
    if request.is_ajax() and request.GET:
        item = str(request.GET.get('categoria'))
        subs = PorSubcategoria.objects.filter(categoria=item)
        my_list = list(subs.values_list('nombre', flat=True))
        json_data = json.dumps(my_list)
    return HttpResponse(json_data, content_type='application/json')


@login_required
@permission_required('core.listar_doc_emit', login_url='/')
def export_xls_comp_emit(request):
    response = HttpResponse(mimetype='application/ms-excel')
    file_name = 'comprobantes_emitidos_%s' % datetime.datetime.now().strftime("%Y%m%d%H%M%S")    
    response['Content-Disposition'] = 'attachment; ' \
                                      'filename=%s' \
                                      '.xls' % file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("comprobantes_emitidos")

    row_num = 0

    columns = [
        (u"Fecha", 3200),
        (u"Tipo", 2000),
        (u"Establecimiento", 1500),
        (u"Pto. Emision", 1500),
        (u"Secuencial", 3000),
        (u"Cliente", 7000),
        (u"RUC", 4000),
        (u"Monto", 3000),
        (u"Clave Acceso", 20000),
        (u"Nro Autorizacion", 13000),
        (u"Estado", 2500),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    
    try:
        documentos_emit = request.session['documentos_emitidos']
    except:
        documentos_emit = []
    
    print 'GENERANDO XSL CON', len(documentos_emit)
    for obj in documentos_emit:
        row_num += 1
        try:
            row = [
                obj.fecha_emision.strftime("%Y-%m-%d"),
                obj.tipo_comprobante,
                obj.establecimiento,
                obj.pto_emision,
                obj.secuencial,
                obj.razon_social_receptor,
                obj.identificacion_receptor,
                obj.monto_total,
                obj.clave_acceso,
                obj.numero_autorizacion,
                obj.estado.nombre_estado]
            
            for col_num in xrange(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
        except NoneType as err:
            print 'NoneType : {0}'.format(err)
        except Exception as e:
            print e
            print("Error inesperado:", sys.exc_info()[0])       

    wb.save(response)
    return response

@login_required
def export_xls_comp_rec(request):
    response = HttpResponse(mimetype='application/ms-excel')
    
    file_name = 'comprobantes_recibidos_%s' % datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    response['Content-Disposition'] = 'attachment; ' \
                                      'filename=%s' \
                                      '.xls' % file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("comprobantes_recibidos")

    row_num = 0

    columns = [
        (u"Fecha", 3400),
        (u"Tipo", 2000),
        (u"Establecimiento", 1500),
        (u"Pto. Emision", 1500),
        (u"Secuencial", 3000),
        (u"Emisor", 6000),
        (u"Monto", 2500),
        (u"Aprobado por", 6000),
        (u"Fuente", 2500),
        (u"Nro Autorizacion", 10000),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1

    try:
        documentos_recib = request.session['documentos_recibidos']
    except:
        documentos_recib = []

    for obj in documentos_recib:
        row_num += 1
        try:
            nombre_ciudad = ''
            if obj.ciudad: nombre_ciudad = obj.ciudad.nombre
            row = [
                obj.fecha_emision.strftime("%Y-%m-%d"),
                obj.tipo_comprobante,
                obj.establecimiento,
                obj.pto_emision,
                obj.secuencial,
                obj.razon_social_emisor,
                obj.monto_total,
                obj.aprobado_por,
                obj.fuente_generacion.nombre,
                obj.numero_autorizacion
            ]
            
            for col_num in xrange(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
        except NoneType as err:
            print 'NoneType: {0}'.format(err)
            add_log_error('ER-Export-XSL-RECIBIDOS', 'NoneType: {0}'.format(err))
            raise err
        except Exception as e:
            print("Error inesperado: {0}".format(e))
            add_log_error('ER-Export-XSL-RECIBIDOS', '{0}'.format(e))
            raise e
    
    wb.save(response)
    return response

@login_required
def export_xls_camp_public(request):
    print 'exportando'
    response = HttpResponse(mimetype='application/ms-excel')
    response['Content-Disposition'] = 'attachment; ' \
                                      'filename=campanias_publicitarias' \
                                      '.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("campanias_publicitarias")

    row_num = 0

    columns = [
        (u"Nombre Campaña", 3500),
        (u"Fecha Creacion", 3500),
        (u"Fecha Publicacion", 3500),
        (u"Tipo", 4500),
        (u"Estado", 2500),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1

    for obj in result_campanias:
        row_num += 1
        try:
            row = [
                obj.nombre,
                obj.fecha_creacion.strftime("%Y-%m-%d"),
                obj.fecha_publicacion.strftime("%Y-%m-%d"),
                'Campania Email' if obj.tipo_campania == 'eml' else 'Campania SMS',
                obj.estado,
            ]
        except NoneType as err:
            print 'NoneType : {0}'.format(err)
        except:
            print("Error inesperado:", sys.exc_info()[0])
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


@login_required
@permission_required('core.nuevo_porcomprobanteretencion', login_url='/')
def export_xls_perfiles(request):
    response = HttpResponse(mimetype='application/ms-excel')
    response['Content-Disposition'] = 'attachment; ' \
                                      'filename=perfiles_usuarios' \
                                      '.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("perfiles_usuarios")

    row_num = 0

    columns = [
        (u"Nombres", 6000),
        (u"Apellidos", 6000),
        (u"Email", 6000),
        (u"Cedula", 4000),
        (u"Estado", 4000),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1

    for obj in perfiles:
        row_num += 1
        try:
            row = [
                obj.nombres,
                obj.apellidos,
                obj.email_principal,
                obj.identificacion,
                obj.estado.nombre_estado,
            ]
        except NoneType as err:
            print 'NoneType : {0}'.format(err)
        except:
            print("Error inesperado:", sys.exc_info()[0])
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response

def increment_banner_count(request):
    if request.is_ajax() and request.GET:
        id_ban = str(request.GET.get('id_banner'))
        Banner.objects.filter(id_banner=id_ban).update(nro_clicks=F("nro_clicks") + 1)
        json_data = json.dumps("exito")

    return HttpResponse(json_data, content_type='application/json')

def increment_print_count_prod(request):
    if request.is_ajax() and request.GET:
        id_prod = str(request.GET.get('id_prod'))
        print Producto.objects.filter(id=id_prod)
        Producto.objects.filter(id=id_prod).update(
            nro_impresiones=F("nro_impresiones") + 1)
        json_data = json.dumps("exito")

    return HttpResponse(json_data, content_type='application/json')

def increment_print_count_cupon(request):
    if request.is_ajax() and request.GET:
        id_cupon = str(request.GET.get('id_cupon'))
        Cupon.objects.filter(id=id_cupon).update(
            nro_impresiones=F("nro_impresiones") + 1)
        json_data = json.dumps("exito")

    return HttpResponse(json_data, content_type='application/json')

'''
Visualizacion de Documentos
'''
def format_last_url(last_url):
    if '/innobee-docs//' in last_url:
        last_url = last_url.replace('/innobee-docs//', '/home/sysadmin/innobee-docs/')
    elif '/argo-docs//' in last_url:
        last_url = last_url.replace('/argo-docs//', '/home/sysadmin/argo-docs/')
    elif '/aron-docs//' in last_url:
        last_url = last_url.replace('/aron-docs//', '/home/sysadmin/aron-docs/')
    return last_url

def open_file(archivo, tipo):
    try:
        print 'INTENTANDO ABRIR', archivo, 'de', tipo  
        file = open(archivo, "rb").read()
        response = HttpResponse(file, content_type='application/%s' % tipo)
        return response
    except Exception as e:
        print e
    return None

def response_file(archivo, original_url, tipo):
    file_parts = archivo.split('/')
    filename = file_parts[len(file_parts)-1]    
    ruc = filename[2:15]
    archivo = '/home/sysadmin/innobee-docs/'+ruc+'/autorizados/'+filename
    print '->INTENTO 1', archivo
    resp = open_file(archivo, tipo)
    if resp is None:
        archivo = '/home/sysadmin/aron-docs/'+ruc+'/autorizados/'+filename
        print '->INTENTO 2', archivo
        resp = open_file(archivo, tipo)
        if resp is None:
            archivo = '/home/sysadmin/argo-docs/'+ruc+'/autorizados/'+filename
            print '->INTENTO 3', archivo
            resp = open_file(archivo, tipo)
            if resp is None:
                raise Http404
            else:
                return resp
        else:
            return resp
    else:
        return resp

@login_required
def view_docs_pdf(request, codigo_original):
    archivo = None
    try:
        documentos = Documento.objects.filter(codigo_original = codigo_original, estado = 1)
        if documentos.count() > 0:
            documento = documentos[0]
            archivo = format_last_url(documento.ruta_documento_pdf.url)
    except Documento.DoesNotExist:
        raise Http404
    
    if archivo is None:
        raise Http404
    
    return response_file(archivo, documento.ruta_documento_pdf.url, 'pdf')

@login_required
def view_docs_xml(request, codigo_original):
    archivo = None
    try:
        documentos = Documento.objects.filter(codigo_original = codigo_original, estado = 1)
        if documentos.count() > 0:
            documento = documentos[0]
            archivo = format_last_url(documento.ruta_documento_xml.url)
    except Documento.DoesNotExist:
        raise Http404

    if archivo is None:
        raise Http404
    
    return response_file(archivo, documento.ruta_documento_xml.url, 'xml')

def view_docs_html(request, codigo_original):
    archivo = None
    
    documento = None
    try:
        documentos = Documento.objects.filter(codigo_original = codigo_original, estado = 1)
        if documentos.count() > 0:
            documento = documentos[0]
            archivo = documentos[0].ruta_documento_otro
    except Documento.DoesNotExist:
        raise Http404
    
    if archivo is None:
        raise Http404
    
    ruc = documento.ruc_emisor
    
    if documento:
        empresa = PorEmpresa.objects.get(ruc = ruc)
    else:
        raise Http404
        
    path = 'innobee-docs'
    if 'argo-docs' in archivo:
        path = 'argo-docs'
    elif 'aron-docs' in archivo:
        path = 'aron-docs'
    
    html = render_to_string('%s/autorizados/%s.html' % (ruc, codigo_original))
    html = html.replace('logo.png',empresa.logotipo.url)
    html = html.replace('%s.png' % codigo_original, '/%s/%s/autorizados/%s.png' % (path, ruc, codigo_original))
    
    try:
        response = HttpResponse(html)
        return response
    except TypeError:
        traceback.print_exc()

    raise Http404

import base64

def get_direct_pdf(request, trama):
    
    archivo = None
    empresa = None

    print 'get_direct_pdf - Procesando trama', trama
    trama_decoded = base64.b64decode(trama.strip()).strip()
    print 'get_direct_pdf - Procesando trama decode', trama_decoded

    try:
        ruc = trama_decoded[:13]
        secuencial = trama_decoded[13:30]
        clave = trama_decoded[30:]
        
        try:
            empresa = PorEmpresa.objects.get(ruc = ruc)
        except:
            print 'No hay empresa para ruc', ruc
            raise Http404
        
        print 'Clave SFPT empresa', empresa.nombre_comercial, ':', clave, 'comparando con', empresa.password_ftp
        if empresa.password_ftp == clave:
            try:
                #FT001001000000001
                if len(secuencial) == 17:
                    tipo = secuencial[:2]
                    estab = secuencial[2:5]
                    ptoemi = secuencial[5:8]
                    secu = secuencial[8:]
                    print tipo, estab, ptoemi, secu
                    if tipo == 'FT': tipo = 'FE'
                    documentos = Documento.objects.filter(tipo_comprobante = tipo,
                                                          establecimiento = estab,
                                                          pto_emision = ptoemi,
                                                          secuencial = secu,
                                                          ruc_emisor = ruc,
                                                          estado = 1)
                    if documentos.count() > 0:
                        documento = documentos[0]
                        archivo = format_last_url(documento.ruta_documento_pdf.url)
                    else:
                        print 'No existe archivo',partes[0],partes[1],partes[2],partes[3]
                else:
                    print 'Nombre incompleto de archivo', secuencial
                    raise Http404
            except Documento.DoesNotExist:
                print 'ERROR 1'
                raise Http404
        else:
            print 'Los datos no coinciden para la empresa', empresa.nombre_comercial
        
        if archivo is None:
            print 'ERROR NO HAY ARCHIVO'
            raise Http404
    except Exception as e:
        print 'ERROR 2', e
        raise Http404
    return response_file(archivo, documento.ruta_documento_pdf.url, 'pdf')


def reportes_estado(request):

    t = datetime.date.today()
    F1 = t.strftime("%Y-%m-%d")
    Pags = request.GET.get('Paginas', '5')
    Pag = request.GET.get('Pagina', '1')
    F2 = request.GET.get('Dias', '0')
    Suc = request.GET.get('Sucursal', '')
    Emi = request.GET.get('Emision', '')
    Sec = request.GET.get('Secuencial', '')
    cantDias = int(F2)
    F2 = (datetime.date.today()-datetime.timedelta(days=cantDias)).strftime("%Y-%m-%d")
    TC = request.GET.get('TipoComp', '5')
    operador = request.user.get_profile()

    empresa = get_object_or_404(PorEmpresa, ruc=operador.ruc_empresa)
    print 'Extrayendo reporte de', empresa.nombre_comercial, ', server', empresa.server_name

    servidor = empresa.server_name
    ruc = get_object_or_404(PorEmpresa, ruc=operador.ruc_empresa).ruc
    tipo = ""
    msg = ""
    Arreglo = ['', '', '', '', '', '']
    Arreglo2 = ['FT', 'NC', 'CR', 'GR', 'ND', '']
    Arreglo[int(cantDias)] = 'selected'

    try:
        if Pags == '':
            Pags = '5'
        Pag = (int(Pag) - 1) * int(Pags)
        if len(Suc) != 0:
            Suc = '0' * (3 - len(Suc)) + Suc
            Suc = "and substring(codigo_original from 16 for 3)='" + Suc + "'"
        if len(Emi) != 0:
            Emi = '0' * (3 - len(Emi)) + Emi
            Emi = " and substring(codigo_original from 19 for 3)='" + Emi + "' "
        if len(Sec) != 0:
            Sec = '0' * (9 - len(Sec)) + Sec
            Sec = " and substring(codigo_original from 22 for 9)='" + Sec + "' "
        if int(TC) != 5:
            tipo = " and substring(codigo_original from 1 for 2) = '" + Arreglo2[int(TC)] + "' "
        if servidor == 'innobee':
            cursor = connections['innobee'].cursor()
        elif servidor == 'dune':
            cursor = connections['dune'].cursor()
        elif servidor == 'duke':
            cursor = connections['duke'].cursor()
        else:
            cursor = connections['test'].cursor()

        query1 = "select fecha_registro,substring(codigo_original from 1 for 2),substring(codigo_original from 16 for 3), substring(codigo_original from 19 for 3),substring(codigo_original from 22 for 9),indicador_rechazo,motivo_rechazo, origen_error,codigo_original from proceso_respuesta_a_empresa inner join proceso_estado on proceso_respuesta_a_empresa.estado=proceso_estado.estado where codigo_respuesta in (select MAX(codigo_respuesta) from proceso_respuesta_a_empresa where substring(codigo_original from 3 for 13) ='" + ruc + "'" + tipo + "and fecha_registro >='" + F2 + "' and fecha_registro <='" + F1 + "' " + Suc + Emi + Sec + " group by codigo_original) order by codigo_respuesta DESC limit " + Pags + " OFFSET " + str(Pag)
        cursor.execute(query1)
        data = cursor.fetchall()

        #print 'DATOS', data
        request.session['datosEstado'] = data
        cursor.close()
    except Exception as e:
        traceback.print_exc()
        print 'Error:', e
        data = []
        msg = "ERROR: %s" % str(e)

    Arreglo2 = ['', '', '', '', '', '']
    Arreglo2[int(TC)] = 'selected'
    context = {
        'result': data,
        'mensage': msg,
        'select': Arreglo,
        'select2': Arreglo2,
        'suc': request.GET.get('Sucursal', ''),
        'emi': request.GET.get('Emision', ''),
        'sec': request.GET.get('Secuencial', ''),
        'pags': Pags,
        'pag': request.GET.get('Pagina', '1'),
    }
    return render_to_response('emisores/reportes_estado.html', context, context_instance=RequestContext(request))

def exportar_reporte_estado(request):
    response = HttpResponse(mimetype='application/ms-excel')
    file_name = 'estado_comprobantes_%s' % datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    response['Content-Disposition'] = 'attachment; ' \
                                      'filename=%s' \
                                      '.xls' % file_name
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Estado_Comprobantes")

    row_num = 0

    columns = [
        (u"Registro", 3200),
        (u"Tipo", 2000),
        (u"Sucursal", 2000),
        (u"Punto_Emision", 3000),
        (u"Secuencial", 4000),
        (u"Estado  ", 2000),
        (u"Motivo", 20000),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1

    try:
        datos = request.session['datosEstado']
    except:
        datos = []

    for obj in datos:
        row_num += 1
        try:

            row = [
                obj[0].strftime("%Y-%m-%d"),
                obj[1],
                obj[2],
                obj[3],
                obj[4],
                obj[5],
                obj[6]
            ]
            for col_num in xrange(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
        except:
            print("error")


    wb.save(response)
    return response

@login_required
@permission_required('core.reporte_innobee', login_url='/')
@decorators.enterprise_profile_required
def reportes_innobee(request):
    template = "emisores/reportes-innobee.html"

    if request.POST:
        form_rep = FrmFiltroRepInnobee(request.POST)
        form_rep.is_valid()
    else:
        ahora = datetime.datetime.now()
        form_rep = FrmFiltroRepInnobee(initial={'mes':ahora.month,'anio':ahora.year})

    rep_filter = er_helpers.ReporteInnobee(request, form_rep)
    results = rep_filter.procesar()

    context = {
        'form_rep': form_rep,
        'results': results,
        'total_emitido': rep_filter.total_emitido,
        'monto_total_emitido': rep_filter.monto_total_emitido,
        'total_recibido': rep_filter.total_recibido,
        'monto_total_recibido': rep_filter.monto_total_recibido,
    }

    return render_to_response(template, context, context_instance=RequestContext(request))

def exportar_reporte_innobee(request):
    response = HttpResponse(mimetype='application/ms-excel')
    file_name = 'reporte_innobee_%s' % datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    response['Content-Disposition'] = 'attachment; ' \
                                      'filename=%s' \
                                      '.xls' % file_name

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("reporte_empresas_innobee")

    row_num = 0

    columns = [
        (u"RUC", 3000),
        (u"Empresa", 8000),
        (u"Total Emitidos", 2500),
        (u"Monto Emitios", 3500),
        (u"Total Recibidos", 2500),
        (u"Monto Recibidos", 3500),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1


    rep_filter = er_helpers.ReporteInnobee(request, None)
    results = rep_filter.procesar()

    for obj in results:
        row_num += 1
        try:
            row = [
                obj.empresa.ruc,
                obj.empresa.razon_social,
                obj.total_emitidos,
                obj.monto_total_emitido,
                obj.total_recibidos,
                obj.monto_total_recibido]

            for col_num in xrange(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
        except NoneType as err:
            print 'NoneType : {0}'.format(err)
        except Exception as e:
            print e
            print("Error inesperado:", sys.exc_info()[0])

    wb.save(response)
    return response

@login_required
def desactivar_duplicados(request):
    helper = er_helpers.FiltroDocumentoHelper()
    count = helper.disable_dupplicates()
    return HttpResponse('Los %d duplicados fueron eliminados' % count)