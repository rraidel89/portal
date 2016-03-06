# -*- encoding: utf-8 -*-
import datetime

from django import forms
from django.forms.fields import DateField
from django.forms.widgets import DateInput
from django.forms.models import inlineformset_factory
from django.forms.util import ErrorList
from django.forms.formsets import BaseFormSet
import re
from django.core.exceptions import ValidationError

from innobee_portal import properties as P
from core.validators import doc_validator
from django.forms.models import BaseInlineFormSet 

from helpers import catalogo_helper, secuencial_helper
import models
import lookups


widget_date = \
    DateField(required=False, input_formats=['%d/%m/%Y','%m/%d/%Y'],
              widget=forms.DateInput(
                  format='%d/%m/%Y', attrs={'placeholder': 'dd/mm/aaaa', 'class': 'datepicker ui-widget ui-widget-content date-field'}))

widget_req_date = \
    DateField(required=True, input_formats=['%d/%m/%Y','%m/%d/%Y'],
              widget=forms.DateInput(
                  format='%d/%m/%Y', attrs={'placeholder': 'dd/mm/aaaa', 'class': 'datepicker ui-widget ui-widget-content date-field'}))

simple_widget_date = \
    DateField(required=False, input_formats=['%d/%m/%Y','%m/%d/%Y'],
              widget=forms.DateInput(
                  format='%d/%m/%Y', attrs={'placeholder': 'dd/mm/aaaa', 'size': '10', 'class':'ui-widget ui-widget-content date-field'}))

widget_custom_date = \
    DateField(required=False, input_formats=['%Y-%m-%d'],
              widget=forms.DateInput(
                  format='%Y-%m-%d', attrs={'placeholder': 'aaaa-mm-dd', 'class': 'datepicker ui-widget ui-widget-content date-field'}))

style_normal_text = 'ui-widget ui-widget-content normal-field'
style_big_text = 'ui-widget ui-widget-content big-field'
style_numeric = 'ui-widget ui-widget-content numeric-field'
style_date = 'ui-widget ui-widget-content date-field'
style_big_date = 'ui-widget ui-widget-content big-date-field'
style_bigest_text = 'ui-widget ui-widget-content bigest-field'
style_very_big_text = 'ui-widget ui-widget-content very-big-field'
style_big_numeric = 'ui-widget ui-widget-content numeric-big-field'

def clean_numeric_field(form, cleaned_data, numeric_field, non_zero=False):
    try:
        numeric_field_obj = cleaned_data.pop(numeric_field)
        if numeric_field_obj:
            if non_zero:
                if numeric_field_obj <= 0:
                    form._errors[numeric_field] = ErrorList(['Este valor debe ser mayor a 0.'])
            else:
                print 'numeric_field_obj', numeric_field_obj
                if numeric_field_obj < 0:
                    form._errors[numeric_field] = ErrorList(['Este valor debe ser positivo.'])
    except:
        pass

'''
----------------------------------------
COMUNES
----------------------------------------
'''

class ConfiguracionFacturaForm(forms.ModelForm):
    
    secuencial_inicial = forms.CharField(max_length=9, min_length=9, required=True)
    
    class Meta:
        model = models.ImpdFacturaConfiguracion
        exclude = (
            'usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')
    
    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super(ConfiguracionFacturaForm, self).__init__(*args, **kwargs)
        try:
            self.fields['establecimiento'].widget.attrs = {'placeholder': 'Ej: 001 (3 dig)', 'class':style_normal_text}
            self.fields['punto_emision'].widget.attrs = {'placeholder': 'Ej: 001 (3 dig)', 'class':style_normal_text}
            self.fields['secuencial_inicial'].widget.attrs = {'placeholder': 'Ej: 000000001 (9 dig)', 'class':style_normal_text}
            self.fields['secuencial_inicial'].label='Secuencial'
            self.fields['descripcion'].widget = forms.HiddenInput()
            self.fields['ruc_empresa'].widget = forms.HiddenInput()
            if initial and 'descripcion' in initial:
                self.prebind(initial['descripcion'], initial['ruc_empresa'])
        except Exception as e:
            print 'ConfiguracionFacturaForm - Error Inicializacion', e
        self.fields.keyOrder = ['establecimiento', 'punto_emision', 'secuencial_inicial',
                                'moneda', 'descripcion', 'ruc_empresa']

    def clean(self):
        '''Required custom validation for the form.'''
        cleaned_data = self.cleaned_data.copy()
        print cleaned_data
        #print 'ESTABLECIMIENTO',  cleaned_data['establecimiento']

        return self.cleaned_data

    def get_secuencial(self):
        cleaned_data = self.cleaned_data.copy()
        return cleaned_data.pop('secuencial_inicial')

    def prebind(self, descripcion, ruc_empresa):
        configuraciones = models.ImpdFacturaConfiguracion.objects.filter(descripcion = descripcion)
        if configuraciones.count() > 0:            
            configuracion = configuraciones[0]
           
            #self.fields['establecimiento'].initial = configuracion.establecimiento
            #self.fields['punto_emision'].initial = configuracion.punto_emision
           # if descripcion == P.CONFIGURACION_FACTURAS: 
           #     self.fields['secuencial_inicial'].initial = secuencial_helper.get_next_secuencial_factura_intern(configuracion)
           # if descripcion == P.CONFIGURACION_GUIASREMISION:
           #    self.fields['secuencial_inicial'].initial = secuencial_helper.get_next_secuencial_guia_remision_intern(configuracion)
           # elif descripcion == P.CONFIGURACION_COMPROSRETENCION:
           #     self.fields['secuencial_inicial'].initial = secuencial_helper.get_next_secuencial_retencion_intern(configuracion)
           # elif descripcion == P.CONFIGURACION_NOTASCREDITO:
            #    self.fields['secuencial_inicial'].initial = secuencial_helper.get_next_secuencial_notacredito_intern(configuracion)
            #elif descripcion == P.CONFIGURACION_NOTASDEBITO:
                #self.fields['secuencial_inicial'].initial = secuencial_helper.get_next_secuencial_nota_debito_intern(configuracion)
            
            self.fields['descripcion'].initial = configuracion.descripcion
            self.fields['moneda'].initial = configuracion.moneda
        else:
            #self.fields['establecimiento'].initial = '001'
            #self.fields['punto_emision'].initial = '001'
            #self.fields['secuencial_inicial'].initial = '000000001'
            self.fields['descripcion'].initial = descripcion
            self.fields['moneda'].initial = P.MONEDA_DOLAR
            self.fields['ruc_empresa'].initial = ruc_empresa
    
    def save(self):
        
        cleaned_data = self.cleaned_data.copy()
        establecimiento = cleaned_data.pop('establecimiento')
        punto_emision = cleaned_data.pop('punto_emision')
        secuencial_inicial = cleaned_data.pop('secuencial_inicial')
        descripcion = cleaned_data.pop('descripcion')
        moneda = cleaned_data.pop('moneda')
        ruc_empresa = cleaned_data.pop('ruc_empresa')
        configuraciones = models.ImpdFacturaConfiguracion.objects.filter(descripcion = descripcion,establecimiento=establecimiento,punto_emision=punto_emision)
        
        if configuraciones.count() == 0:
            configuracion = models.ImpdFacturaConfiguracion()
            configuracion.establecimiento = establecimiento
            configuracion.punto_emision = punto_emision
            configuracion.moneda = moneda
            configuracion.ruc_empresa = ruc_empresa
            configuracion.secuencial_inicial = secuencial_inicial
            configuracion.descripcion = descripcion
            configuracion.save()
            return configuracion
        else:
            return configuraciones[0]

from django.utils.safestring import mark_safe

class CustomerSearchWidget(forms.TextInput):
    def render(self, name=None, value=None, attrs=None):
          
         widget = super(CustomerSearchWidget, self).render(name, value, attrs)
         
         return mark_safe(u'%s&nbsp;&nbsp;<a class="btn btn-primary"'
                         u' onclick="search_customer_inline()"><i class="fa fa-search"></i>&nbsp;</a>'
                         u'&nbsp;<a rel="tooltip" title="Agregar RUC especial." style="cursor:hand;color:#00CCAA"'
                         u' onclick="add_special_ruc(1)"><i class="fa fa-plus"></i>&nbsp;</a>' % widget)

class CustomerSearchWidgetGR(forms.TextInput):
    def render(self, name=None, value=None, attrs=None):
        widget = super(CustomerSearchWidgetGR, self).render(name, value, attrs)
        return mark_safe(u'%s&nbsp;&nbsp;<a class="btn btn-primary"'
                         u' onclick="search_customer_inlineGR()"><i class="fa fa-search"></i>&nbsp;</a>'
                         u'&nbsp;<a rel="tooltip" title="Agregar RUC especial." style="cursor:hand;color:#00CCAA"'
                         u' onclick="add_special_ruc(2)"><i class="fa fa-plus"></i>&nbsp;</a>' % widget)

class ClienteForm(forms.ModelForm):
    
    identificacion = forms.CharField(max_length=20, min_length=3, widget = CustomerSearchWidget())
    email_principal = forms.EmailField()
    email_secundario = forms.EmailField(required=False)
    
    class Meta:
        model = models.ImpdCliente
        exclude = (
            'usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')
    
    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super(ClienteForm, self).__init__(*args, **kwargs)
        try:
            self.fields['tipo_identificacion'].initial = P.TID_CEDULA
            self.fields['identificacion'].widget.attrs = {'placeholder': 'Ej: 179999999001', 'class':style_normal_text}
            self.fields['razon_social'].widget.attrs = {'placeholder': 'Ej: Pedro Paredes', 'class':style_big_text}
            self.fields['email_principal'].widget.attrs = {'placeholder': 'Ej: pparedes@dominio.com',
                                                           'class':style_big_text}
            self.fields['email_secundario'].widget.attrs = {'placeholder': 'Ej: pedro.paredes@otrodominio.com',
                                                            'class':style_big_text}
            self.fields['direccion_comprador'].widget.attrs = {'placeholder': 'Ej: Av. 6 de Diciembre N3-23 y Orellana',
                                                            'class':style_big_text}
            self.fields['ruc_empresa'].widget = forms.HiddenInput()
            self.fields['ruc_empresa'].initial = initial['ruc_empresa']
        except Exception as e:
            print 'ClienteForm - Error Inicializacion', e
    
    def clean(self):
        '''Required custom validation for the form.'''
        cleaned_data = self.cleaned_data.copy()
        
        tipo_identificacion = cleaned_data.pop('tipo_identificacion', None)
        identificacion = cleaned_data.pop('identificacion', None)
        
        if tipo_identificacion == P.TID_CEDULA:
            if not doc_validator.validar_cedula(identificacion):
                self._errors['identificacion'] = ErrorList(['No es una cedula valida.'])
        if tipo_identificacion == P.TID_RUC:
            if not doc_validator.validar_ruc(identificacion):
                self._errors['identificacion'] = ErrorList(['No es un RUC valido.'])
                #TID_PASAPORTE = '06'
                
        return self.cleaned_data
    
    def save(self):
        entity = super(ClienteForm, self).save(commit=False)
        clientes = models.ImpdCliente.objects.filter(tipo_identificacion=entity.tipo_identificacion,
                                                     identificacion=entity.identificacion,
                                                     ruc_empresa=entity.ruc_empresa)
        
        if clientes.count() > 0:
            e1 = clientes[0]
            e1.razon_social = entity.razon_social
            e1.email_principal = entity.email_principal
            e1.email_secundario = entity.email_secundario
            e1.direccion_comprador = entity.direccion_comprador
            e1.save()
            return e1
        else:
            entity.save()
        return entity


class ProductoForm(forms.ModelForm):
    
    nombre_registro = forms.CharField(widget=forms.HiddenInput(), required=False)
    id_registro = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = models.ImpdProducto
        exclude = (
            'usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'ruc_empresa')

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        try:
            self.fields['codigo_principal'].widget = forms.TextInput(attrs={'placeholder':"Ej: CYB00001AB0002", 'class':style_normal_text})
            self.fields['codigo_secundario'].widget.attrs = {'placeholder': 'Ej: AB0002', 'class':style_normal_text}
            self.fields['descripcion'].widget.attrs = {'placeholder': 'Ej: BLUE-RAY SAMSUNG 890', 'class':style_normal_text}
            self.fields['precio_unitario'].widget.attrs = {'placeholder': '0.000000', 'class':style_numeric}
        except Exception as e:
            print 'ItemFacturaForm - Error Inicializacion', e

    def clean(self):
        '''Required custom validation for the form.'''
        cleaned_data = self.cleaned_data.copy()
        clean_numeric_field(self, cleaned_data, 'precio_unitario')
        return self.cleaned_data

    def get_name(self):
        cleaned_data = self.cleaned_data
        name = cleaned_data['nombre_registro']
        return '#' + name
    
    def get_name_id(self):
        cleaned_data = self.cleaned_data
        name = cleaned_data['nombre_registro']
        return '#' + name.replace('_0', '_1')
    
    def get_registro_id(self):
        cleaned_data = self.cleaned_data
        return cleaned_data['id_registro']

class ImpdProductoDetalleAdicionalForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ImpdProductoDetalleAdicionalForm, self).__init__(*args, **kwargs)
        try:
            self.fields['nombre'].widget = forms.TextInput(attrs={'placeholder':"Ej: Color", 'class':style_normal_text})
            self.fields['descripcion'].widget.attrs = {'placeholder': 'Ej: Azul', 'class':style_normal_text}
        except Exception as e:
            print 'ImpdProductoDetalleAdicionalForm - Error Inicializacion', e
    
    class Meta:
        model = models.ImpdProductoDetalleAdicional
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'id_producto')
        
class ImpdProductoImpuestoForm(forms.ModelForm):
    
    class Meta:
        model = models.ImpdProductoImpuesto
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'id_producto')

    def __init__(self, *args, **kwargs):
        super(ImpdProductoImpuestoForm, self).__init__(*args, **kwargs)
        try:
            self.fields['codigo_impuesto'].required = True
            self.fields['codigo_impuesto'].widget.attrs['onchange'] = \
                "catalog_filter(this,'id_codigo_porcentaje','%s','%s');" %\
                (P.CAT_DETALLE_IMPUESTO_CODIGO_IMPUESTO,P.CAT_DETALLE_IMPUESTO_CODIGO_PORCENTAJE)
            self.fields['codigo_porcentaje'].widget.attrs['onchange'] = \
                "catalog_filter(this,'id_tarifa','%s','%s');" %\
                (P.CAT_DETALLE_IMPUESTO_CODIGO_PORCENTAJE, P.CAT_DETALLE_IMPUESTO_TARIFA)
        except Exception as e:
            print 'ImpdProductoImpuestoForm - Error Inicializacion', e
            
ProductoDetalleAdicionalFormSet = inlineformset_factory(models.ImpdProducto, models.ImpdProductoDetalleAdicional,
                                                        ImpdProductoDetalleAdicionalForm, extra=1, max_num=3)

ProductoImpuestoFormSet = inlineformset_factory(models.ImpdProducto, models.ImpdProductoImpuesto,
                                form=ImpdProductoImpuestoForm, extra=1, max_num=8)

'''
----------------------------------------
FACTURAS
----------------------------------------
'''

class FacturaForm(forms.ModelForm):
    
    fecha_emision = widget_req_date

    class Meta:
        model = models.ImpdFactura
        exclude = (
            'usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'estado_pago', 'secuencial',
            'codigo_original', 'total_sin_impuestos', 'total', 'descuento',
            'impuestos', 'id_configuracion', 'id_cliente')

    def __init__(self, request, *args, **kwargs):
        super(FacturaForm, self).__init__(*args, **kwargs)

        self.numericos_comercio =  ['flete_internacional','seguro_internacional','gastos_aduaneros',
                                    'gastos_transporte_otros']

        self.listas_comercio = ['pais_origen','pais_destino','pais_adquisicion']

        campos_comercio_exterior = ['comercio_exterior','inco_term_factura', 'lugar_inco_term','pais_origen','puerto_embarque',
                                    'pais_destino','puerto_destino','pais_adquisicion', 'inco_term_total_sin_impuestos',
                                    'flete_internacional','seguro_internacional','gastos_aduaneros',
                                    'gastos_transporte_otros']

        self.numericos_reembolsos =  ['total_comprobantes_reembolso','total_base_imponible_reembolso',
                                      'total_impuesto_reembolso', 'valor_ret_iva','valor_ret_renta']
        campos_reembolso = ['total_comprobantes_reembolso','total_base_imponible_reembolso','total_impuesto_reembolso',
                            'valor_ret_iva','valor_ret_renta','cod_doc_reembolso']

        try:
            for ct in campos_comercio_exterior:
                if ct in self.numericos_comercio: attr_class = style_numeric
                elif ct in self.listas_comercio: attr_class = 'select_join'
                else: attr_class = style_normal_text
                self.fields[ct].widget.attrs = {'screen': '1', 'class': attr_class}

                if ct == 'comercio_exterior':
                    self.fields[ct].widget = forms.HiddenInput()

            for ct in campos_reembolso:
                if ct in self.numericos_reembolsos: attr_class = style_numeric
                else: attr_class = 'select_join'
                self.fields[ct].widget.attrs = {'screen': '2', 'class': attr_class}

            for cn in self.numericos_comercio:
                self.fields[cn].required = False

            self.fields['inco_term_factura'].label = 'Incoterm'
            self.fields['lugar_inco_term'].label = 'Lugar Incoterm'

            self.fields['ruc_empresa'].widget = forms.HiddenInput()
            self.fields['propina'].widget = forms.TextInput(attrs={'placeholder': '0.00', 'class':style_numeric})
            self.fields['guia_remision'].widget = forms.TextInput(attrs={'placeholder': '000-000-000000000',
                                                                         'class':style_numeric})
        except Exception as e:
            print 'ItemFacturaForm - Error Inicializacion', e

        self.fields.keyOrder = [ 'guia_remision', 'fecha_emision',  'propina', 'ruc_empresa']
        self.fields.keyOrder.extend(campos_comercio_exterior)
        profile = request.user.get_profile()
        if profile.ruc_empresa.reembolsos:
            self.fields.keyOrder.extend(campos_reembolso)

    def clean(self):
        cleaned_data = self.cleaned_data.copy()
        clean_numeric_field(self, cleaned_data, 'propina')
        return self.cleaned_data

    def get_propina(self):
        cleaned_data = self.cleaned_data.copy()
        propina = cleaned_data.pop('propina', 0)
        return propina
    
    def save(self, id_configuracion=None, id_cliente=None, force_insert=False, force_update=False, commit=True):
        entity = super(FacturaForm, self).save(commit)
        if id_configuracion:
            entity.id_configuracion = id_configuracion
        if id_cliente:
            entity.id_cliente = id_cliente
        if entity.inco_term_factura:
            entity.inco_term_factura = entity.inco_term_factura.upper()
        if entity.inco_term_total_sin_impuestos:
            entity.inco_term_total_sin_impuestos = entity.inco_term_total_sin_impuestos.upper()
        return entity

class ItemFacturaForm(forms.ModelForm):
    
    precio_unitario = forms.FloatField(label='P. Unitario', initial=0.0, widget=forms.TextInput(attrs={'class':style_numeric}), required=False)
    precio_total = forms.FloatField(label='P. Total', initial=0.0, widget=forms.TextInput(attrs={'class':style_numeric}), required=False)
    descuento = forms.FloatField(label='Desc.', initial=0.0, required=False)
    
    class Meta:
        model = models.ImpdItemFactura
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'total_sin_impuestos')
    
    def clean(self):
        cleaned_data = self.cleaned_data.copy()
        clean_numeric_field(self, cleaned_data, 'cantidad', True)
        clean_numeric_field(self, cleaned_data, 'descuento')
        return self.cleaned_data
    
    def __init__(self, ruc_empresa, *args, **kwargs):
        self.ruc_empresa = ruc_empresa
        super(ItemFacturaForm, self).__init__(*args, **kwargs)
        try:
            self.fields['id_producto'].label = 'Producto'
            self.fields['id_producto'].widget = lookups.get_producto_factura_lookup_widget( self.ruc_empresa )
            self.fields['descuento'].widget = forms.TextInput(
                attrs={'onkeyup':'recalc_factura();','onchange':'recalc_factura();', 'placeholder': '0.00', 'class':style_numeric})
            self.fields['cantidad'].widget = forms.TextInput(
                attrs={'onkeyup':'recalc_factura();','onchange':'recalc_factura();', 'placeholder': '0.00', 'class':style_numeric})
        except Exception as e:
            print 'ItemFacturaForm - Error Inicializacion', e

        self.fields.keyOrder = ['cantidad', 'id_producto', 'precio_unitario', 'descuento', 'precio_total']

class ImpdFacturaInformacionAdicionalForm(forms.ModelForm):
    
    class Meta:
        model = models.ImpdFacturaInformacionAdicional
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')

    def __init__(self, *args, **kwargs):
        super(ImpdFacturaInformacionAdicionalForm, self).__init__(*args, **kwargs)
        try:
            self.fields['nombre'].widget.attrs = {'placeholder': 'Ej: Telefono'}
            self.fields['valor'].widget.attrs = {'placeholder': 'Ej: 099999999'}
            
            #ruc_transportista = forms.CharField(max_length=13, min_length=10, widget = CustomerSearchWidgetGR())

        except Exception as e:
            print 'ImpdFacturaInformacionAdicionalForm - Error Inicializacion', e

    #def save(self, force_insert=False, force_update=False, commit=True):
       # entity = super(ImpdFacturaInformacionAdicionalForm, self).save(commit)
       # print 'Guardandoooooooooooooooooooooooooooooo'
       # return entity

class FacturaItemsSet(BaseInlineFormSet):

    def __init__(self, ruc_empresa, *args, **kwargs):
        self.ruc_empresa = ruc_empresa
        super(FacturaItemsSet, self).__init__(*args, **kwargs)
        
    def _construct_forms(self):
        self.forms = []
        for i in xrange(self.total_form_count()):
            self.forms.append(self._construct_form(i, ruc_empresa=self.ruc_empresa))

InformacionAdicionalFormSet = inlineformset_factory(models.ImpdFactura, models.ImpdFacturaInformacionAdicional, form=ImpdFacturaInformacionAdicionalForm, extra=1, max_num=15)
ItemFacturaFormSet = inlineformset_factory(models.ImpdFactura, models.ImpdItemFactura, form=ItemFacturaForm, formset=FacturaItemsSet, extra=1, max_num=80)

class ImpdReembolsoForm(forms.ModelForm):

    class Meta:
        model = models.ImpdFactReembolso
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')

    def __init__(self, *args, **kwargs):
        super(ImpdReembolsoForm, self).__init__(*args, **kwargs)
        try:
            self.fields['tipo_identificacion_proveedor_reembolso'].label = 'Tip.Id.'
            self.fields['tipo_identificacion_proveedor_reembolso'].widget.attrs = {'class': 'select_join'}
            self.fields['identificacion_proveedor_reembolso'].label = 'Ident.'
            self.fields['identificacion_proveedor_reembolso'].widget.attrs = {'placeholder': 'Ej: 1000000000',
                                                                              'class': style_big_text}
            self.fields['cod_pais_pago_proveedor_reembolso'].label = 'Pais Prov.'
            self.fields['cod_pais_pago_proveedor_reembolso'].widget.attrs = {'class': 'select_join'}
            self.fields['tipo_proveedor_reembolso'].widget.attrs = {'class': 'select_join'}
            self.fields['tipo_proveedor_reembolso'].label = 'Tipo Prov.'
            self.fields['estab_doc_reembolso'].widget.attrs = {'placeholder': 'Ej: 001','class': style_normal_text}
            self.fields['estab_doc_reembolso'].label = 'Estab.'
            self.fields['estab_doc_reembolso'].max_length=3
            self.fields['estab_doc_reembolso'].min_length=3
            self.fields['pto_emi_doc_reembolso'].widget.attrs = {'placeholder': 'Ej: 001','class': style_normal_text}
            self.fields['pto_emi_doc_reembolso'].label = 'Pto.'
            self.fields['pto_emi_doc_reembolso'].max_length=3
            self.fields['pto_emi_doc_reembolso'].min_length=3
            self.fields['secuencial_doc_reembolso'].widget.attrs = {'placeholder': 'Ej: 000000001',
                                                                    'class': style_big_text}
            self.fields['secuencial_doc_reembolso'].label = 'Secuenc.'
            self.fields['secuencial_doc_reembolso'].max_length=9
            self.fields['secuencial_doc_reembolso'].min_length=9

            self.fields['cod_doc_reembolso'].widget.attrs = {'class': 'select_join'}
            self.fields['cod_doc_reembolso'].label = 'Tip Doc.'
            self.fields['fecha_emision'].widget.attrs = {'placeholder': 'dd/mm/aaaa', 'class': style_big_date}
            self.fields['numero_autorizacion'].widget.attrs = {'class': style_big_text}
            self.fields['numero_autorizacion'].label = '# Autoriz.'
        except Exception as e:
            print 'ImpdReembolsoForm - Error Inicializacion', e

ReembolsosFormSet = inlineformset_factory(models.ImpdFactura, models.ImpdFactReembolso, form=ImpdReembolsoForm, extra=1, max_num=15)

class ImpdImpuestoReembolsoForm(forms.ModelForm):

    class Meta:
        model = models.ImpdFactDetalleImpuestoReembolso
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado','reembolso')

    def __init__(self, *args, **kwargs):
        super(ImpdImpuestoReembolsoForm, self).__init__(*args, **kwargs)
        try:
            self.fields['codigo_reembolso'].label = 'Codig.'
            self.fields['codigo_reembolso'].widget.attrs = {'class': 'select_join'}
            self.fields['codigo_porcentaje_rembolso'].label = 'Porc.%'
            self.fields['codigo_porcentaje_rembolso'].widget.attrs = {'class': 'select_join'}
            self.fields['tarifa_reembolso'].label = 'Tarifa'
            self.fields['tarifa_reembolso'].widget.attrs = {'class': 'select_join'}
            self.fields['impuesto_reembolso'].label = 'Imp.'
            self.fields['impuesto_reembolso'].widget.attrs = {'class': style_numeric}
            self.fields['base_imponible_reembolso'].label = 'Base'
            self.fields['base_imponible_reembolso'].widget.attrs = {'class': style_numeric}

            self.fields['codigo_reembolso'].widget.attrs['onchange'] = \
                        "catalog_filter(this,'codigo_porcentaje_rembolso','%s','%s');" %\
                        (P.CAT_DETALLE_IMPUESTO_REEM_CODIGO_REEMBOLSO,P.CAT_DETALLE_IMPUESTO_REEM_CODIGO_PORCENTAJE)
            self.fields['codigo_porcentaje_rembolso'].widget.attrs['onchange'] = \
                        "catalog_filter(this,'tarifa_reembolso','%s','%s');" % \
                        (P.CAT_DETALLE_IMPUESTO_REEM_CODIGO_PORCENTAJE, P.CAT_DETALLE_IMPUESTO_REEM_TARIFA)

        except Exception as e:
            print 'ImpdReembolsoForm - Error Inicializacion', e

    def get_dict(self):
        cleaned_data = self.cleaned_data.copy()
        return {'codigo_reembolso':cleaned_data['codigo_reembolso'],
                'codigo_porcentaje_rembolso':cleaned_data['codigo_porcentaje_rembolso'],
                'tarifa_reembolso':cleaned_data['tarifa_reembolso'],
                'base_imponible_reembolso':cleaned_data['base_imponible_reembolso'],
                'impuesto_reembolso':cleaned_data['impuesto_reembolso'],}

from django.forms.formsets import formset_factory

ImpdImpuestoReembolsoFormSet = formset_factory(ImpdImpuestoReembolsoForm)

class ImpdFactPagoForm(forms.ModelForm):

    class Meta:
        model = models.ImpdFactPago
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')

    def __init__(self, *args, **kwargs):
        super(ImpdFactPagoForm, self).__init__(*args, **kwargs)
        try:
            self.fields['forma_pago'].label = 'Forma de Pago'
            self.fields['forma_pago'].widget.attrs = {'class': 'select_join'}
            self.fields['total'].widget.attrs = {'class': style_numeric}
            self.fields['plazo'].widget.attrs = {'placeholder': 'Ej: 30', 'class': style_normal_text}
            self.fields['unidad_tiempo'].label = 'Unidad de Tiempo'
            self.fields['unidad_tiempo'].widget.attrs = {'class': 'select_join'}
        except Exception as e:
            print 'ImpdFactPagoForm - Error Inicializacion', e

PagoFormSet = inlineformset_factory(models.ImpdFactura, models.ImpdFactPago, form=ImpdFactPagoForm, extra=1, max_num=15)

'''
----------------------------------------
 GUIA REMISION
----------------------------------------
'''

class GuiaRemisionForm(forms.ModelForm):
    
    fecha_emision = widget_req_date
    fecha_inicio_transporte = widget_date
    fecha_fin_transporte = widget_date
    ruc_transportista = forms.CharField(max_length=13, min_length=5, widget = CustomerSearchWidgetGR())

    class Meta:
        model = models.ImpdGuiaRemision
        exclude = (
            'usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'estado_pago', 'secuencial', 
            'secuencial_number', 'codigo_original', 'id_configuracion')

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super(GuiaRemisionForm, self).__init__(*args, **kwargs)
        try:
            self.fields['ruc_empresa'].widget = forms.HiddenInput()
            self.fields['direccion_partida'].widget.attrs = {'placeholder': 'Ej: Olmedo y Perez Guerrero', 'class':style_big_text}
            self.fields['rise'].widget.attrs = {'placeholder': 'Cuando corresponda'}
            self.fields['razon_social_transportista'].widget.attrs = {'placeholder': 'Ej: Transportes America S.A', 'class':style_big_text}
            self.fields['ruc_transportista'].widget.attrs = {'placeholder': 'Ej: 1799999999001', 'class':style_normal_text}
            self.fields['placa'].widget.attrs = {'placeholder': 'Ej: PCO-000', 'class':style_normal_text}
            self.fields['tipo_identif_transportista'].initial = P.TID_RUC
            self.fields['fecha_inicio_transporte'].required = True
            self.fields['fecha_fin_transporte'].required = True
            
        except Exception as e:
            print 'GuiaRemisionForm - Error Inicializacion', e
        
        self.fields.keyOrder = ['tipo_identif_transportista','ruc_transportista','direccion_partida', 'rise', 'razon_social_transportista',
                                'fecha_inicio_transporte', 'fecha_fin_transporte', 'placa', 'ruc_empresa', 'fecha_emision']



    def clean(self):
        '''Required custom validation for the form.'''
        cleaned_data = self.cleaned_data.copy()
        
        tipo_identif_transportista = cleaned_data.pop('tipo_identif_transportista', None)
        ruc_transportista = cleaned_data.pop('ruc_transportista', None)
        
        if tipo_identif_transportista == P.TID_CEDULA:
            if not doc_validator.validar_cedula(ruc_transportista):
                self._errors['ruc_transportista'] = ErrorList(['No es una cedula valida.'])
        elif tipo_identif_transportista == P.TID_RUC:
            if not doc_validator.validar_ruc(ruc_transportista):
                self._errors['ruc_transportista'] = ErrorList(['No es un RUC valido.'])
        
        return self.cleaned_data
    
    def save(self, id_configuracion=None, force_insert=False, force_update=False, commit=True):
        entity = super(GuiaRemisionForm, self).save(commit)
        if id_configuracion: entity.id_configuracion = id_configuracion
        return entity

class ImpdGuiaRemisionInformacionAdicionalForm(forms.ModelForm):
    
    class Meta:
        model = models.ImpdGRInformacionAdicional
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')

    def __init__(self, *args, **kwargs):
        super(ImpdGuiaRemisionInformacionAdicionalForm, self).__init__(*args, **kwargs)
        try:
            self.fields['nombre'].widget = forms.TextInput(attrs={'placeholder':"Ej: Email", 'class':style_normal_text})
            self.fields['valor'].widget.attrs = {'placeholder': 'Ej: emorales@dominio.com', 'class':style_normal_text}
        except Exception as e:
            print 'ImpdGuiaRemisionInformacionAdicionalForm - Error Inicializacion', e


InformacionAdicionalGuiaRemisionFormSet = inlineformset_factory(models.ImpdGuiaRemision, models.ImpdGRInformacionAdicional, form=ImpdGuiaRemisionInformacionAdicionalForm, extra=1, max_num=15)

class ImpdGuiaRemisionDetalleDestinatarioForm(forms.ModelForm):
    fecha_emi_docum_sustento = widget_req_date
    num_documento_sustento = forms.CharField(label='Numero Documento de Sustento', required=False)
    num_autori_docum_sustento = forms.CharField(label='Numero Autorizacion del Documento de Sustento', min_length=10, max_length=37, required=False)
    codigo_establecimiento_destino = forms.CharField(label='Codigo Establecimiento Destino', min_length=3, max_length=3, required=False)
    #documento_aduanero_unico = forms.CharField(label='Documento Aduanero Unico', max_length=20, required=False)
    
    class Meta:
        model = models.ImpdGRDetalleDestinatario
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'guia_remision')
    
    def __init__(self, ruc_empresa, *args, **kwargs):
        self.ruc_empresa = ruc_empresa
        super(ImpdGuiaRemisionDetalleDestinatarioForm, self).__init__(*args, **kwargs)
        try:
            print 'INICIALIZANDO GUIA REMISION EMPRESA', self.ruc_empresa
            self.fields['destinatario'].widget = lookups.get_destinatario_lookup_widget( self.ruc_empresa )
            self.fields['motivo_traslado'].widget = forms.TextInput(attrs={'placeholder':"Ej: Almacen fuera de la ciudad", 'class':style_big_text})
            self.fields['documento_aduanero_unico'].widget = forms.TextInput(attrs={'placeholder':'Cuando corresponda Ej: 00000000-2014-00000000-S', 'class':style_normal_text})
            self.fields['codigo_establecimiento_destino'].widget = forms.TextInput(attrs={'placeholder':'Cuando Corresponda Ej: 001.', 'class':style_normal_text})
            self.fields['ruta'].widget = forms.TextInput(attrs={'placeholder':'Cuando corresponda Ej: Quito - Guayaquil', 'class':style_normal_text})
            self.fields['num_documento_sustento'].widget.attrs = {'placeholder': 'Cuando corresponda. Ej:000-000-000000000(15 dig)', 'class':style_normal_text}
            self.fields['num_autori_docum_sustento'].widget.attrs = {'placeholder': 'Cuando corresponda Ej:0000000000000000000000000000000000000(10-37 dig)', 'size':'37', 'class':style_big_text}
            self.fields['fecha_emi_docum_sustento'].required = True
        except Exception as e:
            print 'ItemFacturaForm - Error Inicializacion', e
        
        self.fields.keyOrder = ['destinatario', 'motivo_traslado', 'documento_aduanero_unico', 'codigo_establecimiento_destino',
                                'ruta', 'fecha_emi_docum_sustento', 'codigo_documento_sustento', 'num_documento_sustento', 'num_autori_docum_sustento']
    
    
    def clean(self):
        cleaned_data = self.cleaned_data.copy()
        clean_numeric_field(self, cleaned_data, 'cantidad')
        num_documento_sustento = cleaned_data.pop('num_documento_sustento', None)
        if num_documento_sustento:
         try:
            mo=re.match("[0-9][0-9][0-9][-][0-9][0-9][0-9][-][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",num_documento_sustento)
            if(mo.group()):
             print 'OK'
             
         except Exception as e:
            self._errors['num_documento_sustento'] = ErrorList(['El número documento modificado no es correcto. Ej:(000-000-000000000).'])

        
        return self.cleaned_data

    def save(self, guia_remision):
        entity = super(ImpdGuiaRemisionDetalleDestinatarioForm, self).save(commit=False)
        entity.guia_remision = guia_remision
        entity.save()
        return entity

class ImpdGuiaRemisionProductoDestinatarioForm(forms.ModelForm):

    class Meta:
        model = models.ImpdGRProductoDestinatario
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')
    
    def __init__(self, ruc_empresa, *args, **kwargs):
        self.ruc_empresa = ruc_empresa
        super(ImpdGuiaRemisionProductoDestinatarioForm, self).__init__(*args, **kwargs)
        try:
            #print 'INICIALIZANDO CON EMPRESA', self.ruc_empresa
            self.fields['producto'].widget = lookups.get_producto_factura_lookup_widget( self.ruc_empresa )
            self.fields['cantidad'].widget = forms.TextInput(attrs={'placeholder':"0.000000", 'class':style_normal_text})
        except Exception as e:
            print 'ImpdGuiaRemisionProductoDestinatarioForm - Error Inicializacion', e
        
        self.fields.keyOrder = ['cantidad', 'producto']
    
    def clean(self):
        cleaned_data = self.cleaned_data.copy()
        clean_numeric_field(self, cleaned_data, 'cantidad')
        return self.cleaned_data

class GuiaRemisionProductoDestinatarioSet(BaseInlineFormSet):

    def __init__(self, ruc_empresa, *args, **kwargs):
        self.ruc_empresa = ruc_empresa
        super(GuiaRemisionProductoDestinatarioSet, self).__init__(*args, **kwargs)
        
    def _construct_forms(self):
        self.forms = []
        for i in xrange(self.total_form_count()):
            self.forms.append(self._construct_form(i, ruc_empresa=self.ruc_empresa))

ImpdGuiaRemisionProductoDestinatarioFormSet = inlineformset_factory(models.ImpdGRDetalleDestinatario, models.ImpdGRProductoDestinatario,form=ImpdGuiaRemisionProductoDestinatarioForm, formset=GuiaRemisionProductoDestinatarioSet, extra=1, max_num=80)


class ImpdDestinatarioForm(forms.ModelForm):
    id_registro_destinatario = forms.CharField(widget=forms.HiddenInput(),required=False)
    
    class Meta:
        model = models.ImpdGRDestinatario
        exclude = (
            'usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'ruc_empresa', 'guia_remision')

    def __init__(self, *args, **kwargs):
        super(ImpdDestinatarioForm, self).__init__(*args, **kwargs)
        try:
            self.fields['identificacion_destinatario'].widget = forms.TextInput(attrs={'placeholder':"Ej: 1000000001", 'class':style_normal_text})
            self.fields['razon_social_destinatario'].widget = forms.TextInput(attrs={'placeholder':"Ej: Julio Paredes", 'class':style_big_text})
            self.fields['direccion_destinatario'].widget = forms.TextInput(attrs={'placeholder':"Ej: 12 de Octubre y Olmedo", 'class':style_big_text})
        except Exception as e:
            print 'ImpdDestinatarioForm - Error Inicializacion', e
            
    def clean(self):
        '''Required custom validation for the form.'''
        cleaned_data = self.cleaned_data.copy()
        
        #tipo_identif_sujeto_retenido = cleaned_data.pop('tipo_identif_sujeto_retenido', None)
        ruc_sujeto_retenido = cleaned_data.pop('identificacion_destinatario', None)
        
        
        if  doc_validator.validar_cedula_leng_destinatario(ruc_sujeto_retenido):
               if not doc_validator.validar_cedula(ruc_sujeto_retenido):
                self._errors['identificacion_destinatario'] = ErrorList(['No es un cedula valida.'])
               
        if  doc_validator.validar_ruc_leng_destinatario(ruc_sujeto_retenido):
               if not doc_validator.validar_ruc(ruc_sujeto_retenido):
                self._errors['identificacion_destinatario'] = ErrorList(['No es un ruc valido.'])
        if not doc_validator.validar_cedula_leng(ruc_sujeto_retenido) and not doc_validator.validar_ruc_leng(ruc_sujeto_retenido):
            self._errors['identificacion_destinatario'] = ErrorList(['No es una cedula o ruc valida.'])
        
        
        #elif not doc_validator.validar_ruc(ruc_sujeto_retenido):
         #       self._errors['identificacion_destinatario'] = ErrorList(['No es una cedula o RUC valido.'])
        
        #if not doc_validator.validar_cedula_leng(ruc_sujeto_retenido) or not doc_validator.validar_ruc_leng(ruc_sujeto_retenido):
         #       self._errors['identificacion_destinatario'] = ErrorList(['No es una cedula o RUC validos.'])
        
        #elif not doc_validator.validar_ruc(ruc_sujeto_retenido):
         #       self._errors['identificacion_destinatario'] = ErrorList(['No es una cedula o RUC valido.'])
        
        
        return self.cleaned_data       


'''
----------------------------------------
 COMPROBANTE DE RETENCION
----------------------------------------
'''

class ComproRetencionForm(forms.ModelForm):
    
    fecha_emision = widget_req_date
    periodo_fiscal = forms.CharField(label='Periodo Fiscal', min_length=7, max_length=7)
    
    
    class Meta:
        model = models.ImpdComproRetencion
        exclude = (
            'usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'estado_pago', 'secuencial', 
            'secuencial_number', 'codigo_original', 'id_configuracion', 'id_cliente')

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super(ComproRetencionForm, self).__init__(*args, **kwargs)
        try:
            self.fields['ruc_empresa'].widget = forms.HiddenInput()
            self.fields['periodo_fiscal'].widget.attrs = {'placeholder': 'mm/aaaa', 'class':style_date}
        except Exception as e:
            print 'ComproRetencionForm - Error Inicializacion', e

    def clean(self):
        '''Required custom validation for the form.'''
        cleaned_data = self.cleaned_data.copy()
        
        tipo_identif_sujeto_retenido = cleaned_data.pop('tipo_identif_sujeto_retenido', None)
        ruc_sujeto_retenido = cleaned_data.pop('ruc_sujeto_retenido', None)
        periodo_fiscal = cleaned_data.pop('periodo_fiscal', None)
        
        if tipo_identif_sujeto_retenido == P.TID_CEDULA:
            if not doc_validator.validar_cedula(ruc_sujeto_retenido):
                self._errors['ruc_sujeto_retenido'] = ErrorList(['No es una cedula valida.'])
        elif tipo_identif_sujeto_retenido == P.TID_RUC:
            if not doc_validator.validar_ruc(ruc_sujeto_retenido):
                self._errors['ruc_sujeto_retenido'] = ErrorList(['No es un RUC valido.'])
        
        return self.cleaned_data

    def save(self, id_configuracion=None, id_cliente=None, force_insert=False, force_update=False, commit=True):
        entity = super(ComproRetencionForm, self).save(commit)
        if id_configuracion:
            if isinstance(id_configuracion, models.ImpdFacturaConfiguracion):
                entity.id_configuracion = id_configuracion
            else:
                entity.id_configuracion = models.ImpdFacturaConfiguracion.objects.get(pk=id_configuracion)
        if id_cliente:
            if isinstance(id_cliente, models.ImpdCliente):
                entity.id_cliente = id_cliente
            else:
                entity.id_cliente = models.ImpdCliente.objects.get(pk=id_cliente)
        return entity

class ImpdCRETImpuestosForm(forms.ModelForm):
    numero_documento_sustento = forms.CharField(label='Numero Documento Sustento', min_length=15, max_length=15, required=True)
    #fecha_emi_docum_sustento = widget_date
    fecha_emi_docum_sustento = forms.DateField(input_formats=['%d/%m/%Y', '%m/%d/%Y',], widget=forms.DateInput(format = '%d/%m/%Y'),required=True)
    
    class Meta:
        model = models.ImpdCRETImpuestos
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')
    
    def clean(self):
        '''Required custom validation for the form.'''
        print 'CLEANING...'
        super(ImpdCRETImpuestosForm, self).clean()
        cleaned_data = self.cleaned_data.copy()
        clean_numeric_field(self, cleaned_data, 'base_imponible')
        clean_numeric_field(self, cleaned_data, 'valor_retenido')
        clean_numeric_field(self, cleaned_data, 'porcentaje_retener_tmp')
        return self.cleaned_data
    
    def __init__(self, *args, **kwargs):
        super(ImpdCRETImpuestosForm, self).__init__(*args, **kwargs)
        try:
            print 'INICIALIZANDO...'
            self.fields['base_imponible'].widget = forms.TextInput(attrs={'placeholder':"0.00", 'class':style_big_numeric})
            self.fields['valor_retenido'].widget = forms.TextInput(attrs={'placeholder':"0.00", 'class':style_big_numeric})
            self.fields['porcentaje_retener_tmp'].label = '% Retener'
            self.fields['porcentaje_retener_tmp'].widget = forms.TextInput(attrs={'placeholder':"0.00", 'class':style_big_numeric+' input_hide'})
            self.fields['numero_documento_sustento'].widget.attrs = {'placeholder': '000000000000000(15 dig)', 'class':style_very_big_text}
            self.fields['porcentaje_retener'].widget.attrs['onchange'] = "update_field(this,'porcentaje_retener', 'porcentaje_retener_tmp');"
            self.fields['fecha_emi_docum_sustento'].widget.attrs = {'placeholder': 'dd/mm/aaaa', 'class': style_big_date}
            self.fields['codigo_impuesto'].widget.attrs['onchange'] =\
                "updateImpuestos(this,'id_codigo_retencion', 'id_porcentaje_retener', '%s', '%s','%s');"\
                % (P.CAT_DETALLE_IMPUESTO_CODIGO_IMPUESTO,
                   P.CAT_TABLA_19_RETENCION,
                   P.CAT_TABLA_19_A_RETENCION)
            self.fields['codigo_impuesto'].widget.attrs['class'] = 'codigo_impuesto_tmp'
        except Exception as e:
            print 'ImpdCRETImpuestosForm - Error Inicializacion', e
    
    
    
    def clean(self):
        '''Required custom validation for the form.'''
        cleaned_data = self.cleaned_data.copy()
        numero_documento_sustento = cleaned_data.pop('numero_documento_sustento', None)
        
        if numero_documento_sustento:
            try:
                mo=re.match("[0-9]{15}",numero_documento_sustento).group()
            except:
                self._errors['numero_documento_sustento'] = ErrorList(['El número documento sustento no es correcto (15 digitos).'])

        
         
        return self.cleaned_data
    
    

class ImpdCRETInformacionAdicionalForm(forms.ModelForm):
    
    class Meta:
        model = models.ImpdCRETInformacionAdicional
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')

    def __init__(self, *args, **kwargs):
        super(ImpdCRETInformacionAdicionalForm, self).__init__(*args, **kwargs)
        try:
            self.fields['nombre'].widget = forms.TextInput(attrs={'placeholder':"Ej: Email"})
            self.fields['valor'].widget.attrs = {'placeholder': 'Ej: emorales@dominio.com'}
        except Exception as e:
            print 'ImpdCRETInformacionAdicionalForm - Error Inicializacion', e

ImpdCRETImpuestosFormSet = inlineformset_factory(models.ImpdComproRetencion, models.ImpdCRETImpuestos, form=ImpdCRETImpuestosForm, extra=0, max_num=80)
ImpdCRETImpuestosFormSet_crear = inlineformset_factory(models.ImpdComproRetencion, models.ImpdCRETImpuestos, form=ImpdCRETImpuestosForm, extra=1, max_num=80)

InformacionAdicionalCRETFormSet = inlineformset_factory(models.ImpdComproRetencion, models.ImpdCRETInformacionAdicional, form=ImpdCRETInformacionAdicionalForm, extra=1, max_num=15)

'''
----------------------------
CONSULTAS
----------------------------
'''

NUMERO_FILAS = (
    ('5', '5'),
    ('10', '10'),
    ('50', '50'),
)

class ConsultaDocumentoImpdForm(forms.Form):
    fecha_desde = widget_custom_date
    fecha_hasta = widget_custom_date
    secuencial = forms.CharField(label='Secuencial', min_length=9, max_length=9, required=False,
                                widget = forms.TextInput(attrs={'placeholder':"000000000", 'class':'form-control'}))
    identificacion_cliente = forms.CharField(label='Identificacion del Cliente', min_length=6, max_length=13, required=False,
                                widget = forms.TextInput(attrs={'placeholder':"0000000000000", 'class':'form-control'}))
    razon_social_cliente = forms.CharField(label='Razon del Cliente', min_length=5, max_length=60, required=False,
                                widget = forms.TextInput(attrs={'placeholder':"Ej: Pedro Guerra", 'class':'form-control'}))

class ConsultaFacturasForm(ConsultaDocumentoImpdForm):
    filas = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_impd_facturas();'}), initial='5')

class ConsultaGuiasForm(ConsultaDocumentoImpdForm):
    filas = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_impd_guias();'}), initial='5')

class ConsultaRetencionesForm(ConsultaDocumentoImpdForm):
    filas = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_impd_retenciones();'}), initial='5')
    

'''
----------------------------
NOTA DE DEBITO
----------------------------
'''
class NotaDebitoForm(forms.ModelForm):
    
    #fecha_emision = widget_req_date
    #fecha_emision_documento_modificado = widget_date
    fecha_emision = forms.DateField(input_formats=['%d/%m/%Y', '%m/%d/%Y',], widget=forms.DateInput(format = '%d/%m/%Y'),required=True)
    fecha_emision_documento_modificado = forms.DateField(input_formats=['%d/%m/%Y', '%m/%d/%Y',], widget=forms.DateInput(format = '%d/%m/%Y'),required=True)

    numero_documento_modificado = forms.CharField(required=True)
    
    class Meta:
        model = models.ImpdNotaDebito
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'id_configuracion', 'id_cliente', 'codigo_original')

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super(NotaDebitoForm , self).__init__(*args, **kwargs)
        try:
            self.fields['fecha_emision'].widget.attrs = {'placeholder': 'dd/mm/aaaa', 'class':style_date}
            self.fields['ruc_empresa'].widget = forms.HiddenInput()
            self.fields['numero_documento_modificado'].widget.attrs = {'placeholder': 'Ej:000-000-000000000 (15 dig)'}
            #self.fields['fecha_emision_documento_modificado'].required = True
            self.fields['fecha_emision_documento_modificado'].widget.attrs = {'placeholder': 'dd/mm/aaaa', 'class':style_date}
            self.fields['rise'].widget.attrs = {'placeholder': 'Cuando corresponda'}
        except Exception as e:
            print 'NotaDebitoForm - Error Inicializacion', e
            
        self.fields.keyOrder = ['fecha_emision', 'rise', 'codigo_documento_modificado', 
                            'numero_documento_modificado', 'fecha_emision_documento_modificado',
                            'total_sin_impuestos', 'valor_total', 'ruc_empresa']
    
    def save(self, id_configuracion=None, id_cliente=None, force_insert=False, force_update=False, commit=True):
        entity = super(NotaDebitoForm, self).save(commit)
        if id_configuracion: entity.id_configuracion = id_configuracion
        if id_cliente: entity.id_cliente = id_cliente
        return entity
    
    def clean(self):
        '''Required custom validation for the form.'''
        cleaned_data = self.cleaned_data.copy()
        numero_documento_modificado = cleaned_data.pop('numero_documento_modificado', None)
        try:
            mo=re.match("[0-9][0-9][0-9][-][0-9][0-9][0-9][-][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",numero_documento_modificado)
            if(mo.group()):
             print 'OK'
             
        except Exception as e:
            self._errors['numero_documento_modificado'] = ErrorList(['El número documento modificado no es correcto. Ej:(000-000-000000000).'])

        return self.cleaned_data
    
class ImpdNotaDebitoImpuestosForm(forms.ModelForm):
     
    class Meta:
        model = models.ImpdNotaDebitoImpuestos
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')
   
    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super(ImpdNotaDebitoImpuestosForm , self).__init__(*args, **kwargs)
        try:
            self.fields['codigo_impuesto'].widget.attrs['onchange'] = "catalog_filter(this,'id_codigo_porcentaje','%s','%s');" % (P.CAT_DETALLE_IMPUESTO_CODIGO_IMPUESTO,P.CAT_DETALLE_IMPUESTO_CODIGO_PORCENTAJE)
            self.fields['codigo_porcentaje'].widget.attrs['onchange'] = "catalog_filter(this,'id_tarifa','%s','%s', true);" % (P.CAT_DETALLE_IMPUESTO_CODIGO_PORCENTAJE, P.CAT_DETALLE_IMPUESTO_TARIFA)
        except Exception as e:
            print 'ImpdNotaDebitoImpuestosForm - Error Inicializacion', e    
    
class ImpdNotaDebitoMotivosForm(forms.ModelForm):
    
    class Meta:
        model = models.ImpdNotaDebitoMotivos
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')
      
    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super(ImpdNotaDebitoMotivosForm , self).__init__(*args, **kwargs)
        try:
            self.fields['razon'].widget.attrs = {'placeholder': 'Ej: Cambio de Valor'}
            self.fields['valor'].widget.attrs = {'placeholder': 'Ej: 33.12'}
        except Exception as e:
            print 'ImpdNotaDebitoMotivosForm - Error Inicializacion', e

class ImpdNotaDebitoInfoAdicionalForm(forms.ModelForm):
    
    class Meta:
        model = models.ImpdNotaDebitoInfoAdicional
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')

    def __init__(self, *args, **kwargs):
        super(ImpdNotaDebitoInfoAdicionalForm, self).__init__(*args, **kwargs)
        try:
            self.fields['nombre'].widget.attrs = {'placeholder': 'Ej: Telefono'}
            self.fields['valor'].widget.attrs = {'placeholder': 'Ej: 099999999'}
        except Exception as e:
            print 'ImpdNotaDebitoInfoAdicionalForm - Error Inicializacion', e
    
ImpdNDImpuestosFormSet = inlineformset_factory(models.ImpdNotaDebito, models.ImpdNotaDebitoImpuestos, form=ImpdNotaDebitoImpuestosForm, extra=1, max_num=10)
ImpdNDMotivosFormSet   = inlineformset_factory(models.ImpdNotaDebito, models.ImpdNotaDebitoMotivos, form=ImpdNotaDebitoMotivosForm, extra=1, max_num=10)
ImpdNDInfoAdFormSet    = inlineformset_factory(models.ImpdNotaDebito, models.ImpdNotaDebitoInfoAdicional, form=ImpdNotaDebitoInfoAdicionalForm, extra=1, max_num=5)

'''
----------------------------
NUEVO: NOTA DE CREDITO
----------------------------
'''

class NotaCreditoForm(forms.ModelForm):
    
    rise = forms.CharField(max_length=40, required=False)
    #fecha_emi_docum_sustento = widget_date
    fecha_emi_docum_sustento = forms.DateField(input_formats=['%d/%m/%Y', '%m/%d/%Y',], widget=forms.DateInput(format = '%d/%m/%Y'),required=True)
    numero_documento_modificado = forms.CharField(required=True)

    class Meta:
        model = models.ImpdNotaCredito
        exclude = (
            'usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'estado_pago', 'secuencial', 
            'codigo_original', 'total_sin_impuestos', 'id_configuracion', 'id_cliente')

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super(NotaCreditoForm, self).__init__(*args, **kwargs)
        try:
            
            self.fields['ruc_empresa'].widget = forms.HiddenInput()
            self.fields['rise'].widget.attrs = {'placeholder': 'Cuando corresponda'}
            self.fields['numero_documento_modificado'].widget.attrs = {'placeholder': '000-000-000000000 (15 dig)', 'class' : style_normal_text}
            self.fields['fecha_emi_docum_sustento'].widget.attrs = {'placeholder': 'dd/mm/aaaa', 'class':style_date}
            self.fields['fecha_emision'].widget.attrs = {'placeholder': 'dd/mm/aaaa', 'class':style_date}
            
        except Exception as e:
            print 'NotaCreditoForm - Error Inicializacion', e
        self.fields.keyOrder = ['fecha_emision', 'rise', 'codigo_documento_modificado',
                                'numero_documento_modificado', 'fecha_emi_docum_sustento',
                                'valor_modificacion', 'motivo', 'ruc_empresa']

    def save(self, id_configuracion=None, id_cliente=None, force_insert=False, force_update=False, commit=True):
        entity = super(NotaCreditoForm, self).save(commit)
        if id_configuracion: entity.id_configuracion = id_configuracion
        if id_cliente: entity.id_cliente = id_cliente
        return entity
    
    def clean(self):
        '''Required custom validation for the form.'''
        cleaned_data = self.cleaned_data.copy()
        
        numero_documento_modificado = cleaned_data.pop('numero_documento_modificado', None)
        try:
            mo=re.match("[0-9][0-9][0-9][-][0-9][0-9][0-9][-][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",numero_documento_modificado)

            if(mo.group()):
             print 'OK'
             
        except Exception as e:
            self._errors['numero_documento_modificado'] = ErrorList(['El número documento modificado no es correcto. Ej:(000-000-000000000).'])
        
        return self.cleaned_data

class ItemNotaCreditoForm(forms.ModelForm):
    precio_unitario = forms.FloatField(label='P. Unitario', initial=0.0, widget=forms.TextInput(attrs={'class':style_numeric}), required=False)
    precio_total = forms.FloatField(label='P. Total', initial=0.0, widget=forms.TextInput(attrs={'class':style_numeric}), required=False)
    descuento = forms.FloatField(label='Desc.', initial=0.0, required=False)
    
    class Meta:
        model = models.ImpdItemNotaCredito
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado', 'total_sin_impuestos')
    
    def clean(self):
        cleaned_data = self.cleaned_data.copy()
        clean_numeric_field(self, cleaned_data, 'cantidad', True)
        clean_numeric_field(self, cleaned_data, 'descuento')
        return self.cleaned_data
    
    def __init__(self, ruc_empresa, *args, **kwargs):
        self.ruc_empresa = ruc_empresa
        super(ItemNotaCreditoForm, self).__init__(*args, **kwargs)
        try:
            self.fields['id_producto'].label = 'Producto'
            self.fields['id_producto'].widget = lookups.get_producto_factura_lookup_widget( self.ruc_empresa )
            self.fields['descuento'].widget = forms.TextInput(
                attrs={'onkeyup':'recalc_nota_credito();','onchange':'recalc_nota_credito();', 'placeholder': '0.00'})
            self.fields['cantidad'].widget = forms.TextInput(
                attrs={'onkeyup':'recalc_nota_credito();','onchange':'recalc_nota_credito();', 'placeholder': '0.00'})
        except Exception as e:
            print 'ItemNotaCreditoForm - Error Inicializacion', e
            
        self.fields.keyOrder = ['cantidad', 'id_producto', 'precio_unitario', 'descuento', 'precio_total']

class ImpdNotaCreditoInformacionAdicionalForm(forms.ModelForm):
    
    class Meta:
        model = models.ImpdNotaCreditoInformacionAdicional
        exclude = ('usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'estado')

    def __init__(self, *args, **kwargs):
        super(ImpdNotaCreditoInformacionAdicionalForm, self).__init__(*args, **kwargs)
        try:
            self.fields['nombre'].widget.attrs = {'placeholder': 'Ej: Telefono'}
            self.fields['valor'].widget.attrs = {'placeholder': 'Ej: 099999999'}
        except Exception as e:
            print 'ImpdNotaCreditoInformacionAdicionalForm - Error Inicializacion', e

class NotaCreditoItemsSet(BaseInlineFormSet):

    def __init__(self, ruc_empresa, *args, **kwargs):
        self.ruc_empresa = ruc_empresa
        super(NotaCreditoItemsSet, self).__init__(*args, **kwargs)
        
    def _construct_forms(self):
        self.forms = []
        for i in xrange(self.total_form_count()):
            self.forms.append(self._construct_form(i, ruc_empresa=self.ruc_empresa))

InformacionAdicionalNotaCreditoFormSet = inlineformset_factory(models.ImpdNotaCredito, models.ImpdNotaCreditoInformacionAdicional, form=ImpdNotaCreditoInformacionAdicionalForm, extra=1, max_num=15)

ItemNotaCreditoFormSet = inlineformset_factory(models.ImpdNotaCredito, models.ImpdItemNotaCredito, form=ItemNotaCreditoForm, formset=NotaCreditoItemsSet, extra=1, max_num=80)
ItemNotaCreditoFormSet_update = inlineformset_factory(models.ImpdNotaCredito, models.ImpdItemNotaCredito, form=ItemNotaCreditoForm, formset=NotaCreditoItemsSet, extra=0, max_num=80)

class ConsultaNotasCreditoForm(ConsultaDocumentoImpdForm):
    filas = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_impd_notascredito();'}), initial='5')


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

class ConsultaNotasDebitoForm(ConsultaDocumentoImpdForm):
    filas = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_impd_notasdebito();'}), initial='5')
