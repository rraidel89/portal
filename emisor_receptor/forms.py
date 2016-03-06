# -*- encoding: utf-8 -*-

import datetime

from django import forms
from django.forms.widgets import Textarea, TextInput, DateInput
from django.forms.fields import DateField, CharField, EmailField, URLField, ChoiceField
from django.forms.models import ModelChoiceField, ModelForm

from core.models import PorEstado, PorCategoria, PorCiudad, \
    PorFuenteGeneracion, PorPais, PorProvincia, PorSubcategoria, \
    PorTipoEmpresa, PorFuenteRecepcion, BuzDocumento, Cupon, Banner, \
    CampaniaEmail, CampaniaSms, Producto, \
    PorEmpresa, PorOperador, PorDatosEmpresariales

from core import mixins as core_mixins
from core import models as core_models
from core import validators as core_validators

from emisor_receptor import lookups as er_lookups
from dateutil import parser

from innobee_portal import properties as P
from innobee_portal import messages as __

from ckeditor.fields import RichTextField
from django.forms.util import ErrorList

NUMERO_FILAS = (
    ('2', '2'),
    ('5', '5'),
    ('10', '10'),
    ('50', '50'),
    ('100', '100'),
)

ORGANIZADOS_POR = (
    ('', '-----'),
    ('nro_impresiones', 'Más Impresos'),
    ('nro_vistos', 'Más Vistos'),
)

ESTABLECIMIENTO_CHOICES = (
    ('001', '001'),
    ('002', '002'),
    ('003', '003'),
    ('004', '004'),
    ('005', '005'),
    ('006', '006'),
    ('007', '007'),
    ('008', '008'),
    ('009', '009'),
    ('010', '010'),
)

ESTADOS_CHOICES = (
    ('', '----'),
    ('Activo', 'Activo'),
    ('Inactivo', 'Inactivo'),
)

ESTADOS_MAIL_CHOICES = (
    ('', '----------'),
    ('Publicado', 'Publicado'),
    ('Sin Publicar', 'Sin Publicar'),
)

TIPO_CHOICES = (
    ('', '----------'),
    ('ROPA', 'ROPA'),
    ('CALZADO', 'CALZADO'),
)

TIPO_CAMPANIA = (
    ('', '----------'),
    ('eml', 'e-mail'),
    ('sms', 'sms'),
)

TIPO_CUPON_CHOICES = (
    ('', '----------'),
    ('DES', 'DESCUENTO'),
    ('REG', 'REGALO'),
)

POSICION_CHOICES = (
    ('', '----------'),
    ('email_footer', 'email_footer'),
    ('page_footer', 'page_footer'),
    ('barra_lateral', 'barra_lateral'),
    ('main', 'main')
)

PLANTILLAS_CHOICES = (
    ('', '----------'),
    ('azul', 'azul'),
    ('amarilla', 'amarilla'),
    ('roja', 'roja'),
)

PRODUCT_CATEGORIA_CHOICES = (
    ('', '----------'),
    ('ropa', 'ropa'),
    ('calzado', 'calzado'),
)

PRODUCT_SUBCATEGORIA_CHOICES = (
    ('', '----------'),
    ('convers', 'convers'),
    ('casual', 'casual'),
    ('camiseta', 'camiseta'),
    ('chompa', 'chompa'),
)

hoy = datetime.datetime.now()
hoy = hoy.strftime('%Y-%m-%d')

widget_date = \
    DateField(required=False, input_formats=['%d/%m/%Y', '%Y-%m-%d'],
              widget=forms.DateInput(
                  format='%Y-%m-%d', attrs={'class': 'datepicker'
                                                     ' form-control',
                                            'size': '10'}))

widget_text_input = forms.TextInput(attrs={'class': 'form-control'})

widget_text_area = forms.CharField(max_length=250, widget=forms.Textarea(
    attrs={'rows': '4', 'cols': '30', 'class': ' form-control'}))

class BuzDocForm(forms.ModelForm):
    fecha_emision = widget_date
    establecimiento = forms.ChoiceField(choices=ESTABLECIMIENTO_CHOICES)
    categoria_emisor = forms.ModelChoiceField(queryset=core_mixins.get_categorias_empresa(), widget=forms.Select(attrs={'onchange':'cargar_sub_categorias_empresa("id_categoria_emisor","id_subcategoria_emisor");'}), required=True)
    subcategoria_emisor = forms.ModelChoiceField(queryset=core_mixins.get_subcategorias_empresa(), required=True)
    
    class Meta:
        model = BuzDocumento
        exclude = (
            'usuario_actualizacion', 'usuario_creacion', 'fecha_creacion',
            'fecha_actualizacion', 'buzon',)

    def __init__(self, *args, **kwargs):
        super(BuzDocForm, self).__init__(*args, **kwargs)
        fields = ['monto_comprobante', 'ruc_emisor',
                  'fuente_recepcion', 'razon_social_emisor',
                  'numero_autorizacion',
                  'aprobado_por', 'numero_comprobante'
                  ]
        for f in fields:
            self.fields[f].widget.attrs['class'] = 'form-control'
        self.estado = PorEstado.objects.get(nombre_estado='ACTIVO')
        self.fuente_recepcion = PorFuenteRecepcion.objects.get(nombre='PORTAL')
        self.fecha_actualizacion = hoy

class FormComprobantesCargados(forms.Form):
    carg_filas = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_cargados_form();'}), initial='5')
    carg_fecha = widget_date
    carg_tipo_comprobante = CharField(widget=forms.Select(choices=P.TIPOS_DOCUMENTO), required=False)
    carg_numero = CharField(max_length=17, required=False, widget=TextInput(attrs={'size': '10', 'class': 'form-control'}))
    carg_emisor = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Razon social o identificacion'}))

class FiltroDocumento(forms.Form):
    em_filas_emitidos = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_emitidos_form();'}), initial='5')
    em_fecha_desde = widget_date
    em_fecha_hasta = widget_date
    em_establecimiento = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'---', 'style':'width:50px', 'title':'Establecimiento'}))
    em_puntoemi = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'---', 'style':'width:50px', 'title':'Punto Emision'}))
    em_secuencial = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'---------', 'style':'width:100px', 'title':'Secuencial'}))
    em_cliente = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Nombres o identificacion'}))
    em_tipo_documento = CharField(widget=forms.Select(choices=P.TIPOS_DOCUMENTO,attrs={'class':'form-control', 'style':'width:120px'}), required=False)
    em_estado = CharField(widget=forms.Select(choices=P.ESTADOS_CHOICES,attrs={'class':'form-control', 'style':'width:100px'}), required=False)

class FiltroDocumentoRecibidos(forms.Form):
    filas_recibidos = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_recibidos_form();'}), initial='5')
    fecha_desdeR = widget_date
    fecha_hastaR = widget_date
    numeroR = forms.CharField(required=False, widget=widget_text_input)
    emisorR = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Razon social o RUC'}))
    aprobado_porR = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Nombre o parte del nombre'}))
    fuenteR = ModelChoiceField(queryset=PorFuenteGeneracion.objects.filter(estado=core_mixins.get_active_status()),
                               required=False, empty_label='----------')
    tipo_documentoR = CharField(widget=forms.Select(choices=P.TIPOS_DOCUMENTO),
                                required=False)

class FrmSndEmailComp(forms.Form):
    comentario = CharField(required=False, widget=widget_text_input)
    email = CharField(required=False, widget=widget_text_input)


TITULOS_EMPRESA = (
    ('', '----------'),
    ('CIA', 'CIA'),
    ('SA', 'SA'),
)

PERFILES_EMPRESA = (
    ('', '----------'),
    ('CIA', 'CIA'),
    ('SA', 'SA'),
)


class PerfilEmpresa(forms.Form):
    titulo = CharField(widget=TextInput(attrs={'size': '20',
                                               'placeholder': 'Nombre Comercial',
        }))
    ruc = CharField(widget=TextInput(attrs={'placeholder': '1000000000001',
                                            'class': 'form-control',
                                            'readonly': 'readonly'}))
    codigo_empresa = CharField(
        widget=TextInput(attrs={'placeholder': '001',
                                'class': 'form-control',
                                'readonly': 'readonly'}))
    razon_social = CharField(
        widget=TextInput(attrs={'placeholder': 'Nombre Razón Social',
                                'class': 'form-control',
                                'readonly': 'readonly'}))
    email_innobee = EmailField(required=False,
                               widget=TextInput(
                                   attrs={'placeholder': 'empresa@innobee.net',
                                          'class': 'form-control'}))
    perfil = ModelChoiceField(queryset=PorTipoEmpresa.objects.all(),
                              required=False, empty_label='----------')
    representante = EmailField(required=False,
                               widget=TextInput(
                                   attrs={'placeholder': 'empresa@innobee.net',
                                          'class': 'form-control'}))
    '''
    categoria = ModelChoiceField(queryset=PorCategoria.objects.all(),
                                 required=False, empty_label='----------')
    subcategoria = ModelChoiceField(queryset=PorSubcategoria.objects.all(),
                                    required=False, empty_label='----------',
                                    widget=forms.Select(
                                        attrs={'class': 'subcategoria'}))
    '''
    
    categoria = forms.ModelChoiceField(queryset=core_mixins.get_categorias_empresa(), widget=forms.Select(attrs={'onchange':'cargar_sub_categorias("id_categoria","id_subcategoria");'}))
    subcategoria = forms.ModelChoiceField(queryset=core_mixins.get_subcategorias_empresa())
    
    pais = ModelChoiceField(queryset=PorPais.objects.all(), required=False,
                            empty_label='----------')
    provincia = ModelChoiceField(queryset=PorProvincia.objects.all(),
                                 required=False, empty_label='----------')
    ciudad = ModelChoiceField(queryset=PorCiudad.objects.all(), required=False,
                              empty_label='----------')
    calle_principal = CharField(required=False)
    numeracion = CharField(required=False)
    calle_secundaria = CharField(required=False)
    telefono_1 = CharField(required=False)
    telefono_2 = CharField(required=False)
    sitio_web = URLField(required=False)
    email = EmailField(required=False)
    fecha_fundacion = DateField(widget=forms.DateInput(format='%d-%m-%Y'),
                                input_formats=('%d-%m-%Y',), required=False)

    mision = CharField(max_length=140, required=False,
                       widget=Textarea(attrs={'rows': 3, 'cols': 33,
                                              'style': 'height: 200px;',
                                              'placeholder':
                                              'Ingrese la misión empresarial en'
                                              ' máximo 140 caracteres'}))
    vision = CharField(max_length=140, required=False,
                       widget=Textarea(attrs={'rows': 3, 'cols': 33,
                                              'style': 'height: 200px;',
                                              'placeholder':
                                              'Ingrese la visión empresarial en'
                                              ' máximo 140 caracteres'}))
    valores = CharField(max_length=140, required=False,
                        widget=Textarea(attrs={'rows': 3, 'cols': 33,
                                               'style': 'height: 200px;',
                                               'placeholder':
                                               'Ingrese los servicios '
                                               'empresariales separados por '
                                               'comas ","'}))


class PerfilPersona(forms.Form):
    nombres = CharField(required=False,
                        widget=TextInput(attrs={'placeholder': 'Nombres',
                                                'class': 'form-control'}))
    apellidos = CharField(required=False,
                          widget=TextInput(attrs={'placeholder': 'Apellidos',
                                                  'class': 'form-control'}))
    '''
    cedula = CharField(required=False,
                       widget=TextInput(attrs={'placeholder': '100123456',
                                               'class': 'form-control'}))
    ''' 
    '''
    correo = EmailField(required=False,
                        widget=TextInput(
                            attrs={'placeholder': 'usuario@gmail.com',
                                   'class': 'form-control'}))
    '''
    numTelefono = CharField(required=False,
                            widget=TextInput(
                                attrs={'placeholder': '593 555555555',
                                       'class': 'form-control'}))
    numCelular = CharField(required=False,
                           widget=TextInput(
                               attrs={'placeholder': '593959804589',
                                      'class': 'form-control'}))
    '''
    email_innobee = EmailField(required=False,
                               widget=TextInput(
                                   attrs={'placeholder': 'persona@inprese.com',
                                          'class': 'form-control'}))
    '''
    nombre_empresa = CharField(required=False,
                               widget=TextInput(
                                   attrs={'placeholder': 'Mi Empresa',
                                          'class': 'form-control'}))
    direccion = CharField(required=False,
                          widget=TextInput(attrs={'placeholder': '10 de Agosto',
                                                  'class': 'form-control'}))
    direccion_secundaria = CharField(required=False,
                                     widget=TextInput(
                                         attrs={'placeholder': 'Av. Colon',
                                                'class': 'form-control'}))
    pais = ModelChoiceField(queryset=PorPais.objects.all(), required=False,
                            empty_label='----------')
    provincia = ModelChoiceField(queryset=PorProvincia.objects.none(),
                                 required=False, empty_label='----------')
    ciudad = ModelChoiceField(queryset=PorCiudad.objects.none(), required=False,
                              empty_label='----------')
    sector = CharField(required=False,
                       widget=TextInput(
                           attrs={'placeholder': 'Mariana de Jesus',
                                  'class': 'form-control'}))
    codigo_postal = CharField(required=False,
                              widget=TextInput(attrs={'placeholder': 'EC174534',
                                                      'class': 'form-control'}))
    titulo = CharField(required=False,
                       widget=TextInput(attrs={'placeholder': 'Ingeniero civil',
                                               'class': 'form-control'}))
    area_trabajo = CharField(required=False,
                             widget=TextInput(
                                 attrs={'placeholder': 'Construcción',
                                        'class': 'form-control'}))
    carrera_estudio = CharField(required=False,
                                widget=TextInput(
                                    attrs={
                                        'placeholder': 'Ingenieria Comercial',
                                        'class': 'form-control'}))
    lugar_estudio = CharField(required=False,
                              widget=TextInput(
                                  attrs={'placeholder': 'Universidad Central',
                                         'class': 'form-control'}))
    # facebook = URLField(required=False,
    # widget=TextInput(attrs={'placeholder': 'http://',
    # 'class': 'form-control'}))
    # twitter = URLField(required=False,
    # widget=TextInput(attrs={'placeholder': 'http://',
    # 'class': 'form-control'}))
    # linkedIn = URLField(required=False,
    #                         widget=TextInput(attrs={'placeholder': 'http://',
    #                                                 'class': 'form-control'}))
    #     google = URLField(required=False,
    #                       widget=TextInput(attrs={'placeholder': 'http://',
    #                                                 'class': 'form-control'}))

    def filter_provincia(self, data):
        """
        Crea un combo dependiente de la ruta, inserta los destinos de salida
        de una ruta desde la agencia actual
        :param data:
        """
        nombre_pais = data.get('nombre', 0)
        if nombre_pais:
            # se lo realiza con consulta nativa luego se convierte a queryset
            consulta = PorProvincia.objects.filter(pais=nombre_pais)
            # Convierto el queryset a lista python
            pk_list = [p.pk for p in consulta]
            # Agrego el orden que quiero que muestre
            self.fields['provincia'].queryset = pk_list


class CuponFormulario(forms.ModelForm):
    estado = forms.ModelChoiceField(queryset=core_mixins.get_onoff_status(), initial=core_mixins.get_active_status())
    tipo_cupon = forms.ChoiceField(choices=TIPO_CUPON_CHOICES, initial='DES')
    #id_provincia = ModelChoiceField(queryset=PorProvincia.objects.all(), required=False)
    categoria = forms.ModelChoiceField(queryset=core_mixins.get_categorias_producto(), widget=forms.Select(attrs={'onchange':'cargar_sub_categorias("id_categoria","id_sub_categoria");'}))
    sub_categoria = forms.ModelChoiceField(queryset=core_mixins.get_subcategorias_producto())
    fecha_publicacion = widget_date
    fecha_final_publicacion = widget_date
    detalles_cupon = widget_text_area
    detalles_validez = widget_text_area
    
    class Meta:
        model = Cupon
        exclude = ('codigo', 'ruc_empresa', 'nro_impresiones', 'nro_vistos', 'fecha_creacion', 'fecha_actualizacion', 'usuario_actualizacion', 'usuario_creacion', 'id_provincia')

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(CuponFormulario, self).__init__(*args, **kwargs)
        self.fields['titular_cupon'].widget.attrs['class'] = 'form-control'
        self.fields['detalles_cupon'].widget.attrs['class'] = 'form-control'
        self.fields['detalles_validez'].widget.attrs['class'] = 'form-control'

class ProductoForm(forms.ModelForm):
    fecha_publicacion = widget_date
    estado = forms.ModelChoiceField(queryset=core_mixins.get_onoff_status(), initial=core_mixins.get_active_status())
    categoria = forms.ModelChoiceField(queryset=core_mixins.get_categorias_producto(), widget=forms.Select(attrs={'onchange':'cargar_sub_categorias("id_categoria","id_sub_categoria");'}))
    sub_categoria = forms.ModelChoiceField(queryset=core_mixins.get_subcategorias_producto())
    detalles_producto = widget_text_area
    url_compra = widget_text_area

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        self.fields['codigo_sku'].widget.attrs['class'] = 'form-control'
        self.fields['codigo_sku'].help_text = 'El CODIGO SKU es la propia CODIFICACION que usted le da a este producto'
        self.fields['titulo'].widget.attrs['class'] = 'form-control'
    
    class Meta:
        model = Producto
        exclude = ('ruc_empresa', 'fecha_creacion', 'nro_impresiones', 'nro_vistos', 'fecha_actualizacion',
                   'usuario_actualizacion', 'usuario_creacion', 'codigo')

class BannerForm(forms.ModelForm):
    estado = forms.ModelChoiceField(queryset=core_mixins.get_onoff_status(), initial=core_mixins.get_active_status())
    fecha_creacion = widget_date
    fecha_publicacion = widget_date

    def __init__(self, *args, **kwargs):
        super(BannerForm, self).__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs['class'] = 'form-control'
        self.fields['impresiones'].widget.attrs['class'] = 'form-control'
        self.fields['impresiones'].initial = 1000
        self.fields['url_banner_apunta'].widget.attrs['class'] = 'form-control'

    class Meta:
        model = Banner
        exclude = ('ruc_empresa', 'nro_vistos', 'impresiones_restantes', 'fecha_creacion', 'fecha_actualizacion', 'usuario_actualizacion', 'usuario_creacion')

from ckeditor.widgets import CKEditorWidget

class CampaniaEmailForm(forms.ModelForm):
    estado = forms.ModelChoiceField(queryset=core_mixins.get_onoff_status(), initial=core_mixins.get_active_status())
    fecha_publicacion = widget_date
    
    url_apunta_banner_superior = forms.URLField(label='Su sitio Web o la direccion de su Promocion',required=True)
    texto = forms.CharField(widget=CKEditorWidget())
    
    class Meta:
        model = CampaniaEmail
        exclude = ('ruc_empresa', 'codigo', 'fecha_creacion', 'fecha_actualizacion', 'usuario_actualizacion', 'usuario_creacion')

    def __init__(self, *args, **kwargs):
        super(CampaniaEmailForm, self).__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs['class'] = 'form-control'
        self.fields['url_apunta_banner_superior'].widget.attrs['class'] = 'form-control'
        self.fields['subject_email'].widget.attrs['class'] = 'form-control'

    def clean_fecha_publicacion(self):
        fecha_publicacion = self.cleaned_data['fecha_publicacion']
        if fecha_publicacion < datetime.date.today():
            raise forms.ValidationError('Fecha de publicación incorrecta. Seleccione una en el futuro')
        return fecha_publicacion

class CampaniaSMSForm(forms.ModelForm):
    estado = forms.ModelChoiceField(queryset=core_mixins.get_onoff_status(), initial=core_mixins.get_active_status())
    fecha_publicacion = forms.CharField(widget=forms.DateInput(format='%Y-%m-%d hh:ii', attrs={'class': 'datetimepicker form-control', 'size': '10'}))
    mensaje = widget_text_area

    class Meta:
        model = CampaniaSms
        exclude = ('ruc_empresa', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_actualizacion', 'tipo_campania')

    def __init__(self, *args, **kwargs):
        super(CampaniaSMSForm, self).__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs['class'] = 'form-control'


class FormFiltroCupon(forms.Form):
    cup_fecha_inicio = widget_date
    cup_fecha_fin = widget_date
    cup_tipo = forms.ChoiceField(choices=TIPO_CUPON_CHOICES, required=False)
    cup_categoria = forms.ModelChoiceField(queryset=core_mixins.get_categorias_producto(), widget=forms.Select(attrs={'onchange':'cargar_sub_categorias("id_cup_categoria","id_cup_sub_categoria");'}), required=False)
    cup_sub_categoria = forms.ModelChoiceField(queryset=core_mixins.get_subcategorias_producto(), required=False)
    cup_estado = forms.ModelChoiceField(queryset=core_mixins.get_onoff_status(), initial=core_mixins.get_active_status(), required=False)
    cup_filas_cupones = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_cupones_form();'}), initial='5')
    cup_organizados_por = CharField(widget=forms.Select(choices=ORGANIZADOS_POR), required=False)
    
    def __init__(self, *args, **kwargs):
        super(FormFiltroCupon, self).__init__(*args, **kwargs)

class FormFiltroBanner(forms.Form):
    ban_fecha_inicio = widget_date
    ban_fecha_fin = widget_date
    ban_nombre = CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    ban_estado = forms.ModelChoiceField(queryset=core_mixins.get_onoff_status(), initial=core_mixins.get_active_status(), required=False)
    ban_ruc = CharField(required=False, widget=forms.TextInput())
    ban_filas_banner = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_banners_form();'}), initial='5')

class FormFiltroProducto(forms.Form):
    pro_fecha_inicio = widget_date
    pro_fecha_fin = widget_date
    pro_categoria = forms.ModelChoiceField(queryset=core_mixins.get_categorias_producto(), widget=forms.Select(attrs={'onchange':'cargar_sub_categorias("id_pro_categoria","id_pro_sub_categoria");'}), required=False)
    pro_sub_categoria = forms.ModelChoiceField(queryset=core_mixins.get_subcategorias_producto(), required=False)    
    pro_nombre_producto = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Nombre o parte del nombre'}))
    pro_estado = forms.ModelChoiceField(queryset=core_mixins.get_onoff_status(), initial=core_mixins.get_active_status(), required=False)
    pro_codigo = CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pro_filas_producto = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_productos_form();'}), initial='5')

class FormFiltroEmail(forms.Form):
    fecha_envio = widget_date
    nombre = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Nombre o parte del nombre'}))
    estado = forms.ChoiceField(choices=ESTADOS_MAIL_CHOICES, required=False)
    filas_email = CharField(widget=forms.Select(choices=NUMERO_FILAS),
                            required=False)

class FormFiltroSMS(forms.Form):
    fecha_envio = widget_date
    nombre = CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'form-control'}))

    estado = forms.ChoiceField(choices=ESTADOS_CHOICES, required=False)
    filas_sms = CharField(widget=forms.Select(choices=NUMERO_FILAS),
                          required=False)

class FormFiltroCampanias(forms.Form):
    cam_fecha_inicio = widget_date
    cam_fecha_fin = widget_date
    cam_nombre = CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Nombre o parte del nombre'}))
    cam_estado = forms.ModelChoiceField(queryset=core_mixins.get_onoff_status(), initial=core_mixins.get_active_status(), required=False)
    cam_tipo = forms.ChoiceField(TIPO_CAMPANIA, required=False)
    cam_filas_campanias = forms.ChoiceField(choices=NUMERO_FILAS,\
                            widget=forms.Select(attrs={'onchange':'filter_campanias_form();'}), initial='5')

class FrmFiltroRepGen(forms.Form):
    fecha_inicio = widget_date
    fecha_fin = widget_date
    tipo_comprobante = CharField(widget=forms.Select(choices=P.TIPOS_DOCUMENTO), required=False, initial=P.TIP_DOC_FACTURA)

class FrmFiltroRepInv(forms.Form):
    fecha_inicio = widget_date
    fecha_fin = widget_date
    identificacion = CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tipo_comprobante = CharField(widget=forms.Select(choices=P.TIPOS_DOCUMENTO), required=False, initial=P.TIP_DOC_FACTURA)

class FrmFiltroRepGlob(forms.Form):
    widget_select = forms.Select(attrs={'class': 'categoria'})
    fecha_inicio = widget_date
    fecha_fin = widget_date
    categoria = ModelChoiceField(queryset=PorCategoria.objects.all(),
                                 required=False, empty_label='----------',
                                 widget=widget_select)
    subcategoria = ModelChoiceField(queryset=PorSubcategoria.objects.all(),
                                    required=False, empty_label='----------',
                                    widget=widget_select)
    ciudad = ModelChoiceField(queryset=PorCiudad.objects.all(), required=False,
                              empty_label='----------')
    provincia = ModelChoiceField(queryset=PorProvincia.objects.all(),
                                 required=False, empty_label='----------')

class PorOperadorForm(ModelForm):
    
    pregunta_1 = forms.ChoiceField(choices=[(k, v) for k, v in P.PREGUNTAS_PREDEFINIDAS_CHOICES],
                                            label='Pregunta #1 (Predefinida)', required=True)
    
    class Meta:
        model = PorOperador
        widgets = {
            'direccion': TextInput(
                attrs={'size': '15', 'class': 'form-control'}),
            'telefono_principal': TextInput(
                attrs={'size': '12', 'class': 'form-control'}),
            'telefono_secundario': TextInput(
                attrs={'size': '12', 'class': 'form-control'}),
            'email_principal': TextInput(
                attrs={'size': '17', 'class': 'form-control'}),
            'email_secundario': TextInput(
                attrs={'size': '17', 'class': 'form-control'}),
            'nombres': TextInput(attrs={'size': '17', 'class': 'form-control'}),
            'apellidos': TextInput(
                attrs={'size': '17', 'class': 'form-control'}),
            'identificacion': TextInput(
                attrs={'size': '17', 'class': 'form-control'}),
            'perfil_facebook': widget_text_input,
            'perfil_twitter': widget_text_input,
            'perfil_linkedid': widget_text_input,
            'perfil_googleplus': widget_text_input,
            'titulo_profesional': widget_text_input,
            'carrera': widget_text_input,
            'lugar_estudio': widget_text_input,
            'area_trabajo': widget_text_input,
            'pregunta_2': widget_text_input,
            'respuesta_1': widget_text_input,
            'respuesta_2': widget_text_input,

        }
        exclude = ('fecha_creacion',
                   'fecha_actualizacion', 'usuario_creacion',
                   'usuario_actualizacion', 'estado',
                   'ruc_empresa', 'user')
    
    def __init__(self, *args, **kwargs):
        super(PorOperadorForm, self).__init__(*args, **kwargs)
        self.fields['email_principal'].widget.attrs['readonly'] = 'readonly'
        self.fields['identificacion'].widget.attrs['readonly'] = 'readonly'
        self.fields['tipo_identificacion'].widget.attrs['readonly'] = 'readonly'
        
class PorEmpresaForm(forms.ModelForm):
    fecha_fundacion = DateField(widget=DateInput(format='%d/%m/%Y'), input_formats=('%d/%m/%Y',), required=False)
    categoria_emisor = forms.ModelChoiceField(queryset=core_mixins.get_categorias_empresa(), widget=forms.Select(attrs={'onchange':'cargar_sub_categorias_empresa("id_categoria_emisor","id_subcategoria_emisor");'}), required=True)
    subcategoria_emisor = forms.ModelChoiceField(queryset=core_mixins.get_subcategorias_empresa(), required=True)
    pais = forms.ModelChoiceField(queryset=core_mixins.get_paises(), widget=forms.Select(attrs={'onchange':'cargar_provincias_pais();'}), required=True)
    provincia = forms.ModelChoiceField(queryset=core_mixins.get_provincias(), widget=forms.Select(attrs={'onchange':'cargar_ciudades_provincia();'}), required=True)
    ciudad = forms.ModelChoiceField(queryset=core_mixins.get_ciudades(), required=True)
    
    class Meta:
        model = PorEmpresa
        widgets = {
            'calle_principal': TextInput(attrs={'size': '15'}),
            'calle_secundaria': TextInput(attrs={'size': '15'}),
            'numeracion': TextInput(attrs={'size': '10'}),
            'telefono_principal': TextInput(attrs={'size': '10'}),
            'extension_principal': TextInput(attrs={'size': '5'}),
            'telefono_secundario': TextInput(attrs={'size': '10'}),
            'extension_secundaria': TextInput(attrs={'size': '5'}),
            'mision': Textarea(attrs={'rows': 3, 'cols': 33,
                                      'style': 'height: 200px;',
                                      'placeholder':
                                          'Ingrese la misión empresarial en máximo 140 caracteres'}),
            'vision': Textarea(attrs={'rows': 3, 'cols': 33,
                                      'style': 'height: 200px;',
                                      'placeholder':
                                          'Ingrese la misión empresarial en máximo 140 caracteres'}),
            'valores': Textarea(attrs={'rows': 3, 'cols': 33,
                                       'style': 'height: 200px;',
                                       'placeholder':
                                           'Ingrese los servicios empresarial separados por comas ","'}),
        }
        exclude = ('fecha_inicio_contrato',
                   'fecha_fin_contrato', 'fecha_creacion',
                   'fecha_actualizacion', 'usuario_creacion',
                   'usuario_actualizacion', 'estado',
                   'codigo_contribuyente_especial', 'obligado_contabilidad',
                   'sincronizado', 'usuario_ftp', 'password_ftp')

    def __init__(self, *args, **kwargs):
        super(PorEmpresaForm, self).__init__(*args, **kwargs)
        self.fields['nombre_comercial'].widget.attrs['readonly'] = 'readonly'
        self.fields['ruc'].widget.attrs['readonly'] = 'readonly'
        self.fields['razon_social'].widget.attrs['readonly'] = 'readonly'
        self.fields['codigo_empresa'].widget.attrs['readonly'] = 'readonly'
        
        fields = ['nombre_comercial', 'ruc', 'razon_social', 'codigo_empresa',
                  'email_principal',
                  'representante_legal', 'fecha_fundacion', 'calle_principal',
                  'calle_secundaria',
                  'numeracion', 'telefono_principal', 'extension_principal',
                  'telefono_secundario',
                  'extension_secundaria', 'direccion_matriz', 'pagina_web',
                  'email_secundario', 'fax',
                  'perfil_facebook', 'perfil_twitter', 'perfil_linkedid',
                  'perfil_googleplus',
        ]
        for f in fields:
            self.fields[f].widget.attrs['class'] = 'form-control'

        self.fields['extension_principal'].widget.attrs['placeholder'] = 'Ext'
        self.fields['extension_secundaria'].widget.attrs['placeholder'] = 'Ext'

class PorOperadorIncompleteForm(ModelForm):
      
    perfil_facebook = URLField(required=False, widget=TextInput(attrs={'size': '128', 'class': 'form-control'}))
    perfil_twitter = URLField(required=False, widget=TextInput(attrs={'size': '128', 'class': 'form-control'}))
    perfil_linkedid = URLField(required=False, widget=TextInput(attrs={'size': '128', 'class': 'form-control'}))
    perfil_googleplus = URLField(required=False, widget=TextInput(attrs={'size': '128', 'class': 'form-control'}))
    pais = forms.ModelChoiceField(queryset=core_mixins.get_paises(), widget=forms.Select(attrs={'onchange':'cargar_provincias_pais();'}), required=True)
    provincia = forms.ModelChoiceField(queryset=core_mixins.get_provincias(), widget=forms.Select(attrs={'onchange':'cargar_ciudades_provincia();'}), required=True)
    ciudad = forms.ModelChoiceField(queryset=core_mixins.get_ciudades(), required=True)
    email = forms.EmailField(required=True, widget = TextInput(attrs={'size': '128', 'class': 'form-control'}))
    telefono = forms.IntegerField(required=True, widget = TextInput(attrs={'size': '12', 'class': 'form-control'}))
    extension = forms.IntegerField(required=True, widget = TextInput(attrs={'size': '6', 'class': 'form-control'}))
    telefono_celular = forms.IntegerField(required=True, widget = TextInput(attrs={'size': '12', 'class': 'form-control'}))
    
    class Meta:
        model = PorDatosEmpresariales
        widgets = {
            'direccion_matriz': TextInput(attrs={'size': '64', 'class': 'form-control'}),
            'razon_social': TextInput(attrs={'size': '128', 'class': 'form-control'}),
            'ruc': TextInput(attrs={'size': '13', 'class': 'form-control'}),            
            'cargo': widget_text_input,
            'pagina_web': widget_text_input,
        }
        exclude = ('fecha_creacion', 'operador',
                   'fecha_actualizacion', 'usuario_creacion',
                   'usuario_actualizacion', 'estado')
    
    def __init__(self, *args, **kwargs):
        super(PorOperadorIncompleteForm, self).__init__(*args, **kwargs)
        
        self.fields['obligado_contabilidad'].required = True
        self.fields['contribuyente_especial'].required = True
        self.fields['usa_facturacion_electronica'].required = True
        self.fields['categoria'].required = True
        self.fields['direccion_matriz'].required = True
        self.fields['ciudad'].required = True
        self.fields['provincia'].required = True
        self.fields['pais'].required = True
        
    
    def clean(self):
        
        try:
            ruc = self.cleaned_data['ruc']
            if ruc:
                validador = core_validators.ValidadorDocumento()
                if not validador.validar_ruc(ruc):
                    self._errors['ruc'] = ErrorList(['El RUC es incorrecto'])
        except Exception as e:
            print e
            self._errors['ruc'] = ErrorList(['El RUC de la Empresa es requerido'])
        
        try:
            perfil_facebook = self.cleaned_data['perfil_facebook']
        except:
            perfil_facebook = None
        
        try:
            perfil_twitter = self.cleaned_data['perfil_twitter']
        except:
            perfil_twitter = None
        
        try:
            perfil_linkedid = self.cleaned_data['perfil_linkedid']
        except:
            perfil_linkedid = None
        try:
            perfil_googleplus = self.cleaned_data['perfil_googleplus']
        except:
            perfil_googleplus = None
        
        if perfil_twitter or perfil_facebook or perfil_linkedid or perfil_googleplus:
            pass
        else:
            self._errors['perfil_facebook'] = ErrorList(['Al menos una red social es requerida'])
        
        return self.cleaned_data

class FrmFiltroRepInnobee(forms.Form):
    anio = forms.IntegerField(required=True)
    mes = forms.ChoiceField(choices=P.MESES_CHOICES, required=True)
