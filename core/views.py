# Create your views here.
# -*- encoding: utf-8 -*-
import datetime
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.shortcuts import render_to_response
from django.template.context import RequestContext, Context
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, Count

from core.models import Banner, CampaniaEmail, CampaniaSms, Producto, Cupon
from emisor_receptor.forms import FormFiltroBanner, FormFiltroEmail, FormFiltroSMS, FormFiltroCupon, FormFiltroProducto, FormFiltroCampanias
from innobee_util.mail_chimp import reporte_campania

from emisor_receptor import helpers as er_helpers

hoy = datetime.datetime.now()
hoy = hoy.strftime('%Y-%m-%d')

#queries_cupones_aux_camp = [Q()]
@login_required
def cupones_descuento(request):
    template = "emisores/cupones.html"
    
    if request.POST:
        frm_filtro_cupon = FormFiltroCupon(request.POST)
        frm_filtro_cupon.is_valid()
    else:
        frm_filtro_cupon = FormFiltroCupon()
        
    cupon_helper = er_helpers.FiltroCuponHelper(request, frm_filtro_cupon)
    cupones_empresa = cupon_helper.process(is_public=False)
    
    context = {'frm_cupon': frm_filtro_cupon,
               'cupones_empresa': cupones_empresa,
               'cant_cupones': cupon_helper.cantidad,
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))

@login_required
@permission_required('core.listar_productos', login_url='/')
def productos_interes(request):
    template = "emisores/productos.html"
    if request.POST:
        frm_filtro_productos = FormFiltroProducto(request.POST)
        frm_filtro_productos.is_valid()
    else:
        frm_filtro_productos = FormFiltroProducto()
        
    prod_helper = er_helpers.FiltroProductoHelper(request, frm_filtro_productos)
    productos_interes = prod_helper.process(is_public=False)
    
    context = {'frm_productos': frm_filtro_productos,
               'productos_interes': productos_interes,
               'cant_productos': prod_helper.cantidad
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))

@login_required
@permission_required('core.listar_campania_email', login_url='/')
def campania_publicidad(request):
    template = "emisores/publicidad.html"
    
    fecha_actual_gmt = datetime.datetime.now()

    if request.POST:
        frm_filtro_campanias_sms = FormFiltroCampanias(request.POST)
        frm_filtro_campanias_sms.is_valid()
    else:
        frm_filtro_campanias_sms = FormFiltroCampanias()
        
    camp_sms_helper = er_helpers.FiltroCampaniasHelper(request, frm_filtro_campanias_sms, page_name='page_sms')
    campania_sms = camp_sms_helper.process_sms()
    
    if request.POST:
        frm_filtro_campanias_email = FormFiltroCampanias(request.POST)
        frm_filtro_campanias_email.is_valid()
    else:
        frm_filtro_campanias_email = FormFiltroCampanias()
        
    camp_email_helper = er_helpers.FiltroCampaniasHelper(request, frm_filtro_campanias_email, page_name='page_email')
    campania_email = camp_email_helper.process_email()
    
    # BANNERS INI ---------
    if request.POST:
        form_banner = FormFiltroBanner(request.POST)
        form_banner.is_valid()
    else:
        form_banner = FormFiltroBanner()
        
    ban_helper = er_helpers.FiltroBannerHelper(request, form_banner)
    banners_empresa = ban_helper.process()
    # BANNERS FIN ---------

    for item in campania_email:
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

    for item in campania_sms:
        if item.fecha_publicacion > fecha_actual_gmt:
            item.editable = True
        else:
            item.editable = False

    context = {'form_banner': form_banner,
               'form_email': frm_filtro_campanias_email,
               'form_sms': frm_filtro_campanias_sms,
               'banners_empresa': banners_empresa,
               'campania_email': campania_email,
               'campania_sms': campania_sms,
               'cant_banners': ban_helper.cantidad,
               'cant_email': camp_email_helper.cantidad,
               'cant_sms': camp_sms_helper.cantidad,
    }

    return render_to_response(template, context,
                              context_instance=RequestContext(request))

@login_required
@permission_required('core.nuevo_porcomprobanteretencion', login_url='/')
def firma_electronica(request):
    template = "emisores/firma-electronica.html"
    context = {}
    return render_to_response(template, context,
                              context_instance=RequestContext(request))

def filtro_email(frm_filtro):

    queries = []

    if frm_filtro.cleaned_data['fecha_envio']:
        queries += [
            Q(fecha_publicacion=frm_filtro.cleaned_data['fecha_envio'])
        ]
    if frm_filtro.cleaned_data['nombre']:
        queries += [
            Q(nombre__contains=frm_filtro.cleaned_data['nombre'])
        ]
    if frm_filtro.cleaned_data['estado']:
        queries += [
            Q(estado=frm_filtro.cleaned_data['estado'])
        ]
    return queries


def filtro_sms(frm_filtro):
    queries = []

    if frm_filtro.cleaned_data['fecha_envio']:
        queries += [
            Q(fecha_publicacion=frm_filtro.cleaned_data['fecha_envio'])
        ]
    if frm_filtro.cleaned_data['nombre']:
        queries += [
            Q(nombre__contains=frm_filtro.cleaned_data['nombre'])
        ]
    if frm_filtro.cleaned_data['estado']:
        queries += [
            Q(estado=frm_filtro.cleaned_data['estado'])
        ]
    return queries
