# Create your views here.
# -*- encoding: utf-8 -*-
from django.views.generic import ListView, UpdateView

from innobee_util.util import LoggedInMixin
from mixins import IMPDCreateViewMixin, IMPDUpdateViewMixin
from core import mixins

from django.contrib import messages

import models
import forms
import datetime
import helpers
import traceback

from innobee_portal import properties as P

'''
-------------------------------------
FACTURAS
-------------------------------------
'''

class ListadoFactura(LoggedInMixin, ListView):
    model = models.ImpdFactura
    template_name = 'emisores/imprenta_digital/factura/lista-facturas.html'
 
    def get_queryset(self):
        queryset = super(ListadoFactura,self).get_queryset()
        helper = helpers.FiltroFacturasHelper(self.request, forms.ConsultaFacturasForm())
        return helper.process()
    
    def get_context_data(self, **kwargs):
        ctx = super(ListadoFactura, self).get_context_data(**kwargs)
        ctx['search_form'] = forms.ConsultaFacturasForm()
        return ctx

class CrearFacturaView(IMPDCreateViewMixin):
    model = models.ImpdFactura
    form_class = forms.FacturaForm
    template_name = 'emisores/imprenta_digital/factura/crear-factura.html'
    success_url = '/imprenta-digital/facturas/'

    def __init__(self):
        super(CrearFacturaView, self).__init__(P.CONFIGURACION_FACTURAS)

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = None
        form = forms.FacturaForm(request, initial={'ruc_empresa': self.get_current_empresa(),
                'fecha_emision':datetime.date.today(), 'descripcion':'Facturas'})

        item_factura_form = forms.ItemFacturaFormSet(self.request.user.get_profile().ruc_empresa)
        info_adicional_form = forms.InformacionAdicionalFormSet()
        reembolso_factura_form = forms.ReembolsosFormSet()
        pago_factura_form = forms.PagoFormSet()
        self.clear_session()
        return self.render_to_response(
            self.get_context_data(form=form,
                                  item_factura_form=item_factura_form,
                                  info_adicional_form=info_adicional_form,
                                  reembolso_factura_form=reembolso_factura_form,
                                  pago_factura_form=pago_factura_form))

    def clear_session(self):
        counter = 0
        while True:
            try:
                del self.request.session['impuestos-reembolso-%d' % counter]
                counter += 1
            except:
                break
        print 'SESION DE IMPUESTOS REEMBOLSO BORRADA'

    def get_context_data(self, **kwargs):
        ctx = super(CrearFacturaView, self).get_context_data(**kwargs)
        ctx['producto_form'] = forms.ProductoForm()
        ctx['detalle_adicional_producto_form'] = forms.ProductoDetalleAdicionalFormSet()
        ctx['impuestos_producto_form'] = forms.ProductoImpuestoFormSet()
        ctx['cliente_form'] = forms.ClienteForm(initial={'ruc_empresa': self.get_current_empresa()})
        ctx['total_sin_impuestos'] = 0
        ctx['total_con_impuestos'] = 0
        ctx['total_descuentos'] = 0
        ctx['total_impuestos'] = 0
        return ctx

class ActualizarFacturaView(IMPDUpdateViewMixin):
    model = models.ImpdFactura
    form_class = forms.FacturaForm
    template_name = 'emisores/imprenta_digital/factura/crear-factura.html'
    success_url = '/imprenta-digital/facturas/'

    def __init__(self):
        super(ActualizarFacturaView, self).__init__(P.CONFIGURACION_FACTURAS)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = forms.FacturaForm(request, instance=self.object)
        item_factura_form = forms.ItemFacturaFormSet(self.request.user.get_profile().ruc_empresa, instance=self.object)
        info_adicional_form = forms.InformacionAdicionalFormSet(instance=self.object)
        reembolso_factura_form = forms.ReembolsosFormSet(instance=self.object)
        pago_factura_form = forms.PagoFormSet(instance=self.object)
        self.fill_imp_reem_session(reembolso_factura_form)
        return self.render_to_response(
            self.get_context_data(form=form,
                                  item_factura_form=item_factura_form,
                                  info_adicional_form=info_adicional_form,
                                  reembolso_factura_form=reembolso_factura_form,
                                  pago_factura_form=pago_factura_form))

    def fill_imp_reem_session(self, formset):
        if formset:
            counter = 0
            for form in formset:
                impuestos_reem = models.ImpdFactDetalleImpuestoReembolso.objects.filter(reembolso = form.instance)
                lista_impuestos_data = []
                for instance in impuestos_reem:
                    print '<--- CARGANDO CON', instance
                    data = {
                        'codigo_reembolso': instance.codigo_reembolso,
                        'codigo_porcentaje_rembolso': instance.codigo_porcentaje_rembolso,
                        'tarifa_reembolso': instance.tarifa_reembolso,
                        'base_imponible_reembolso': instance.base_imponible_reembolso,
                        'impuesto_reembolso': instance.impuesto_reembolso,
                    }
                    print '>--- CARGADO ', data
                    lista_impuestos_data.append(data)
                self.request.session['impuestos-reembolso-%d' % counter] = lista_impuestos_data

                counter += 1

    def get_object(self, queryset=None):
        obj = models.ImpdFactura.objects.get(id=self.kwargs['id'])
        return obj
    
    def get_context_data(self, **kwargs):
        ctx = super(ActualizarFacturaView, self).get_context_data(**kwargs)
        ctx['producto_form'] = forms.ProductoForm()
        ctx['detalle_adicional_producto_form'] = forms.ProductoDetalleAdicionalFormSet()
        ctx['impuestos_producto_form'] = forms.ProductoImpuestoFormSet()
        ctx['cliente_form'] = forms.ClienteForm(initial={'ruc_empresa': self.get_current_empresa()}, instance=self.object.id_cliente)
        ctx['total_sin_impuestos'] = self.object.total_sin_impuestos
        ctx['total_con_impuestos'] = self.object.total
        ctx['total_descuentos'] = self.object.descuento
        ctx['total_impuestos'] = self.object.impuestos
        return ctx

'''
-------------------------------------
GUIAS DE REMISION
-------------------------------------
'''

class ListadoGuiaRemision(LoggedInMixin, ListView):
    model = models.ImpdGuiaRemision
    template_name = 'emisores/imprenta_digital/guiaremision/lista-guias.html'
 
    def get_queryset(self):
        queryset = super(ListadoGuiaRemision,self).get_queryset()
        helper = helpers.FiltroGuiasHelper(self.request, forms.ConsultaGuiasForm())
        return helper.process()

    def get_context_data(self, **kwargs):
        ctx = super(ListadoGuiaRemision, self).get_context_data(**kwargs)
        ctx['search_form'] = forms.ConsultaGuiasForm()
        return ctx
       
class CrearGuiaRemisionView(IMPDCreateViewMixin):
    model = models.ImpdGuiaRemision
    form_class = forms.GuiaRemisionForm
    template_name = 'emisores/imprenta_digital/guiaremision/crear-guia.html'
    success_url = '/imprenta-digital/guiasremision/'

    def __init__(self):
        super(CrearGuiaRemisionView, self).__init__(P.CONFIGURACION_GUIASREMISION)
    
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalles_destinatario_form = forms.ImpdGuiaRemisionDetalleDestinatarioForm(self.get_current_empresa())
        productos_detalles_destinatario_form = forms.ImpdGuiaRemisionProductoDestinatarioFormSet(self.get_current_empresa())
        info_adicional_form = forms.InformacionAdicionalGuiaRemisionFormSet(initial=[{'nombre':'Email'},])
        return self.render_to_response(
            self.get_context_data(form=form,
                                  detalles_destinatario_form=detalles_destinatario_form,
                                  productos_detalles_destinatario_form=productos_detalles_destinatario_form,
                                  info_adicional_form=info_adicional_form))
    
    def get_context_data(self, **kwargs):
        ctx = super(CrearGuiaRemisionView, self).get_context_data(**kwargs)
        ctx['producto_form'] = forms.ProductoForm()
        ctx['detalle_adicional_producto_form'] = forms.ProductoDetalleAdicionalFormSet()
        ctx['impuestos_producto_form'] = forms.ProductoImpuestoFormSet()
        ctx['destinatario_form'] = forms.ImpdDestinatarioForm()
        return ctx

class ActualizarGuiaRemisionView(IMPDUpdateViewMixin):
    model = models.ImpdGuiaRemision
    form_class = forms.GuiaRemisionForm
    template_name = 'emisores/imprenta_digital/guiaremision/crear-guia.html'
    success_url = '/imprenta-digital/guiasremision/'

    def __init__(self):
        super(ActualizarGuiaRemisionView, self).__init__(P.CONFIGURACION_GUIASREMISION)
    
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        destinatario_entity = self.object.get_destinatarios()[0]
        detalles_destinatario_form = forms.ImpdGuiaRemisionDetalleDestinatarioForm(self.get_current_empresa(), instance=destinatario_entity)
        productos_detalles_destinatario_form = forms.ImpdGuiaRemisionProductoDestinatarioFormSet(self.get_current_empresa(), instance=destinatario_entity)
        info_adicional_form = forms.InformacionAdicionalGuiaRemisionFormSet(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form,
                                  detalles_destinatario_form=detalles_destinatario_form,
                                  productos_detalles_destinatario_form=productos_detalles_destinatario_form,
                                  info_adicional_form=info_adicional_form))
    
    def get_object(self, queryset=None):
        obj = models.ImpdGuiaRemision.objects.get(id=self.kwargs['id'])
        return obj
    
    def get_context_data(self, **kwargs):
        ctx = super(ActualizarGuiaRemisionView, self).get_context_data(**kwargs)
        ctx['producto_form'] = forms.ProductoForm()
        ctx['detalle_adicional_producto_form'] = forms.ProductoDetalleAdicionalFormSet()
        ctx['impuestos_producto_form'] = forms.ProductoImpuestoFormSet()
        ctx['destinatario_form'] = forms.ImpdDestinatarioForm()
        return ctx

'''
-------------------------------------
RETENCIONES
-------------------------------------
'''

class ListadoComproRetencion(LoggedInMixin, ListView):
    model = models.ImpdComproRetencion
    template_name = 'emisores/imprenta_digital/comproretencion/lista-retenciones.html'
 
    def get_queryset(self):
        queryset = super(ListadoComproRetencion,self).get_queryset()
        helper = helpers.FiltroRetencionesHelper(self.request, forms.ConsultaRetencionesForm())
        return helper.process()
    
    def get_context_data(self, **kwargs):
        ctx = super(ListadoComproRetencion, self).get_context_data(**kwargs)
        ctx['search_form'] = forms.ConsultaRetencionesForm()
        return ctx

class CrearComproRetencionView(IMPDCreateViewMixin):
    model = models.ImpdComproRetencion
    form_class = forms.ComproRetencionForm
    template_name = 'emisores/imprenta_digital/comproretencion/crear-retencion.html'
    success_url = '/imprenta-digital/retenciones/'

    def __init__(self):
        super(CrearComproRetencionView, self).__init__(P.CONFIGURACION_COMPROSRETENCION)

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        impuestos_form = forms.ImpdCRETImpuestosFormSet_crear()
        info_adicional_form = forms.InformacionAdicionalCRETFormSet()
        return self.render_to_response(
            self.get_context_data(form=form,
                                  impuestos_form=impuestos_form,
                                  info_adicional_form=info_adicional_form))

    def get_context_data(self, **kwargs):
        ctx = super(CrearComproRetencionView, self).get_context_data(**kwargs)
        ctx['cliente_form'] = forms.ClienteForm(initial={'ruc_empresa': self.get_current_empresa()})
        return ctx

class ActualizarComproRetencionView(IMPDUpdateViewMixin):
    model = models.ImpdComproRetencion
    form_class = forms.ComproRetencionForm
    template_name = 'emisores/imprenta_digital/comproretencion/crear-retencion.html'
    success_url = '/imprenta-digital/retenciones/'

    def __init__(self):
        super(ActualizarComproRetencionView, self).__init__(P.CONFIGURACION_COMPROSRETENCION)

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        impuestos_form = forms.ImpdCRETImpuestosFormSet(instance = self.object)
        info_adicional_form = forms.InformacionAdicionalCRETFormSet(instance = self.object)
        return self.render_to_response(
            self.get_context_data(form=form,
                                  impuestos_form=impuestos_form,
                                  info_adicional_form=info_adicional_form))

    def get_object(self, queryset=None):
        obj = models.ImpdComproRetencion.objects.get(id=self.kwargs['id'])
        return obj

    def get_context_data(self, **kwargs):
        ctx = super(ActualizarComproRetencionView, self).get_context_data(**kwargs)
        ctx['cliente_form'] = forms.ClienteForm(initial={'ruc_empresa': self.get_current_empresa()},
                                                instance = self.object.id_cliente)
        return ctx


'''
-------------------------------------
NOTAS DE DEBITO
------------------------------------
'''

class ListadoNotaDebito(LoggedInMixin, ListView):
    model = models.ImpdNotaDebito
    template_name = 'emisores/imprenta_digital/notadebito/lista-notasdebito.html'
 
    def get_queryset(self):
        queryset = super(ListadoNotaDebito,self).get_queryset()
        helper = helpers.FiltroNotasDebitoHelper(self.request, forms.ConsultaNotasDebitoForm())
        return helper.process()

    def get_context_data(self, **kwargs):
        ctx = super(ListadoNotaDebito, self).get_context_data(**kwargs)
        ctx['search_form'] = forms.ConsultaNotasDebitoForm()
        return ctx

class CrearNotaDebitoView(IMPDCreateViewMixin):
    model = models.ImpdNotaDebito
    form_class = forms.NotaDebitoForm
    template_name = 'emisores/imprenta_digital/notadebito/crear-notadebito.html'
    success_url = '/imprenta-digital/notasdebito/'
    
    def __init__(self):
        super(CrearNotaDebitoView, self).__init__(P.CONFIGURACION_NOTASDEBITO)
    
    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        infoImpuestos = forms.ImpdNDImpuestosFormSet()
        infoMotivos = forms.ImpdNDMotivosFormSet()
        info_adicional_form = forms.ImpdNDInfoAdFormSet()
        return self.render_to_response(
            self.get_context_data(form=form,infoImpuestos=infoImpuestos,infoMotivos=infoMotivos,
                                  info_adicional_form=info_adicional_form))
    
    def get_context_data(self, **kwargs):
        ctx = super(CrearNotaDebitoView, self).get_context_data(**kwargs)
        ctx['cliente_form'] = forms.ClienteForm(initial={'ruc_empresa': self.get_current_empresa()})
        ctx['total_sin_impuestos'] = 0
        ctx['valor_total'] = 0
        return ctx

class ActualizarNotaDebitoView(IMPDUpdateViewMixin):
    model = models.ImpdNotaDebito
    form_class = forms.NotaDebitoForm
    template_name = 'emisores/imprenta_digital/notadebito/crear-notadebito.html'
    success_url = '/imprenta-digital/notasdebito/'
    
    def __init__(self):
        super(ActualizarNotaDebitoView, self).__init__(P.CONFIGURACION_NOTASDEBITO)

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        infoImpuestos = forms.ImpdNDImpuestosFormSet(instance = self.object)
        infoMotivos = forms.ImpdNDMotivosFormSet(instance = self.object)
        info_adicional_form = forms.ImpdNDInfoAdFormSet(instance = self.object)
        return self.render_to_response(
            self.get_context_data(form=form,infoImpuestos=infoImpuestos,infoMotivos=infoMotivos,
                                  info_adicional_form=info_adicional_form))
    
    def get_context_data(self, **kwargs):
        ctx = super(ActualizarNotaDebitoView, self).get_context_data(**kwargs)
        ctx['cliente_form'] = forms.ClienteForm(initial={'ruc_empresa': self.get_current_empresa()},
                                                instance = self.object.id_cliente)
        ctx['total_sin_impuestos'] = self.object.total_sin_impuestos
        ctx['valor_total'] = self.object.valor_total
        return ctx
    
    def get_object(self, queryset=None):
        obj = models.ImpdNotaDebito.objects.get(id=self.kwargs['id'])
        return obj

'''
-------------------------------------
COMUNES
-------------------------------------
'''

def factura_preview(request, id):
    helper = helpers.IMPDFacturaHelper(request)
    return helper.ver_xml(id)

def guiaremision_preview(request, id):
    helper = helpers.IMPDGuiaRemisionHelper(request)
    return helper.ver_xml(id)

def retencion_preview(request, id):
    helper = helpers.IMPDComprobanteRetencionHelper(request)
    return helper.ver_xml(id)

def factura_desactivar(request, id):
    helper = helpers.IMPDFacturaHelper(request)
    return helper.desactivar(id)

def guiaremision_desactivar(request, id):
    helper = helpers.IMPDGuiaRemisionHelper(request)
    return helper.desactivar(id)

def retencion_desactivar(request, id):
    helper = helpers.IMPDComprobanteRetencionHelper(request)
    return helper.desactivar(id)

def notadebito_preview(request, id):
    helper = helpers.IMPDNotaDebitoHelper(request)
    return helper.ver_xml(id)

def notadebito_desactivar(request, id):
    helper = helpers.IMPDNotaDebitoHelper(request)
    return helper.desactivar(id)

def factura_pdf(request, id):
    helper = helpers.IMPDFacturaHelper(request)
    return helper.to_pdf(id)

def guiaremision_pdf(request, id):
    helper = helpers.IMPDGuiaRemisionHelper(request)
    return helper.to_pdf(id)

def retencion_pdf(request, id):
    helper = helpers.IMPDComprobanteRetencionHelper(request)
    return helper.to_pdf(id)

def notadebito_pdf(request, id):
    helper = helpers.IMPDNotaDebitoHelper(request)
    return helper.to_pdf(id)

def notacredito_pdf(request, id):
    helper = helpers.IMPDNotaCreditoHelper(request)
    return helper.to_pdf(id)

'''
----------------------------
NUEVO: NOTA DE CREDITO
----------------------------
'''

class ListadoNotaCredito(LoggedInMixin, ListView):
    model = models.ImpdNotaCredito
    template_name = 'emisores/imprenta_digital/notacredito/lista-notascredito.html'
    
    def get_queryset(self):
        queryset = super(ListadoNotaCredito,self).get_queryset()
        helper = helpers.FiltroNotasCreditoHelper(self.request, forms.ConsultaNotasCreditoForm())
        return helper.process()
    
    def get_context_data(self, **kwargs):
        ctx = super(ListadoNotaCredito, self).get_context_data(**kwargs)
        ctx['search_form'] = forms.ConsultaNotasCreditoForm()
        return ctx

class CrearNotaCreditoView(IMPDCreateViewMixin):
    model = models.ImpdNotaCredito
    form_class = forms.NotaCreditoForm
    template_name = 'emisores/imprenta_digital/notacredito/crear-notacredito.html'
    success_url = '/imprenta-digital/notascredito/'
    
    def __init__(self):
        super(CrearNotaCreditoView, self).__init__(P.CONFIGURACION_NOTASCREDITO)
    
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        item_notacredito_form = forms.ItemNotaCreditoFormSet(self.request.user.get_profile().ruc_empresa)
        info_adicional_form = forms.InformacionAdicionalNotaCreditoFormSet()
        return self.render_to_response(
            self.get_context_data(form=form,
                                  item_notacredito_form=item_notacredito_form,
                                  info_adicional_form=info_adicional_form))

    def get_context_data(self, **kwargs):
        ctx = super(CrearNotaCreditoView, self).get_context_data(**kwargs)
        ctx['producto_form'] = forms.ProductoForm()
        ctx['detalle_adicional_producto_form'] = forms.ProductoDetalleAdicionalFormSet()
        ctx['impuestos_producto_form'] = forms.ProductoImpuestoFormSet()
        ctx['cliente_form'] = forms.ClienteForm(initial={'ruc_empresa': self.get_current_empresa()})
        ctx['total_sin_impuestos'] = 0
        ctx['total_con_impuestos'] = 0
        ctx['total_descuentos'] = 0
        ctx['total_impuestos'] = 0
        return ctx

class ActualizarNotaCreditoView(IMPDUpdateViewMixin):
    model = models.ImpdNotaCredito
    form_class = forms.NotaCreditoForm
    template_name = 'emisores/imprenta_digital/notacredito/crear-notacredito.html'
    success_url = '/imprenta-digital/notascredito/'
    
    def __init__(self):
        super(ActualizarNotaCreditoView, self).__init__(P.CONFIGURACION_NOTASCREDITO)
    
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        item_notacredito_form = forms.ItemNotaCreditoFormSet_update(self.request.user.get_profile().ruc_empresa,
                                                             instance=self.object)
        info_adicional_form = forms.InformacionAdicionalNotaCreditoFormSet(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form,
                                  item_notacredito_form=item_notacredito_form,
                                  info_adicional_form=info_adicional_form))

    def get_context_data(self, **kwargs):
        ctx = super(ActualizarNotaCreditoView, self).get_context_data(**kwargs)
        ctx['producto_form'] = forms.ProductoForm()
        ctx['detalle_adicional_producto_form'] = forms.ProductoDetalleAdicionalFormSet()
        ctx['impuestos_producto_form'] = forms.ProductoImpuestoFormSet()
        ctx['cliente_form'] = forms.ClienteForm(initial={'ruc_empresa': self.get_current_empresa()},
                                                instance=self.object.id_cliente)
        ctx['total_sin_impuestos'] = 0
        ctx['total_con_impuestos'] = 0
        ctx['total_descuentos'] = 0
        ctx['total_impuestos'] = 0
        return ctx
    
    def get_object(self, queryset=None):
        obj = models.ImpdNotaCredito.objects.get(id=self.kwargs['id'])
        return obj

def notacredito_preview(request, id):
    helper = helpers.IMPDNotaCreditoHelper(request)
    return helper.ver_xml(id)

def notacredito_desactivar(request, id):
    helper = helpers.IMPDNotaCreditoHelper(request)
    return helper.desactivar(id)


'''
----------------------------
NUEVO-FIN: NOTA DE CREDITO
----------------------------
'''
from django.http import HttpResponseRedirect
from emisor_receptor.helpers import cambiar_estado_comprobante_emitido

def anular_comprobante(request, tipo_comprobante, comprobante_id, codigo_anulacion):
    url_resp = ''
    try:
        print 'Anulando', comprobante_id
        if tipo_comprobante == 'FE':
            url_resp = 'facturas'
            documento = models.ImpdFactura.objects.get(pk=comprobante_id)
        elif tipo_comprobante == 'CR':
            url_resp =  'retenciones'
            documento = models.ImpdComproRetencion.objects.get(pk=comprobante_id)
        elif tipo_comprobante == 'NC':
            url_resp =  'notascredito'
            documento = models.ImpdNotaCredito.objects.get(pk=comprobante_id)
        elif tipo_comprobante == 'ND':
            url_resp =  'notasdebito'
            documento = models.ImpdNotaDebito.objects.get(pk=comprobante_id)
        elif tipo_comprobante == 'GR':
            url_resp =  'guiasremision'
            documento = models.ImpdGuiaRemision.objects.get(pk=comprobante_id)
        
        documento.estado = mixins.get_anulado_status()
        documento.save(user = request.user)
        
        cambiar_estado_comprobante_emitido(request.user.username, tipo_comprobante,
                                           documento.codigo_original, codigo_anulacion, True)
    except Exception as e:
        traceback.print_exc()        
        messages.error(request, 'Comprobante no anulado por ' + str(e))
        return HttpResponseRedirect('/imprenta-digital/%s/' % url_resp)
    
    messages.success(request, 'Comprobante %s deshabilitado.' % documento.secuencial)
    return HttpResponseRedirect('/imprenta-digital/%s/' % url_resp)
