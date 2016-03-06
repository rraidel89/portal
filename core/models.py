# -*- coding: UTF-8 -*-
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.forms import ModelForm
from django.forms.widgets import TextInput
from django.forms.widgets import Textarea, DateInput
from django.forms.fields import DateField
from django.utils.encoding import smart_str
from validatedfile.fields import ValidatedFileField

from innobee_portal import properties as P
#from innobee_util.tareas_programadas import send_sms_prog, crear_campania_email
from innobee_util.tareas_programadas import crear_campania_email

import mixins
from django.core.validators import URLValidator

from django.conf import settings
import authhacks

from tasks import enviar_SMS_campania

from encrypt_fields import EncryptedField

# manejar tipos de extensiones xls, xlsx, csv

content_types_hojas_calc = ['application/vnd.ms-excel',
                               'application/vnd.openxmlformats-officedocument.'
                               'spreadsheetml.sheet',
                               'text/csv'
]

# manejar tipos de extensiones para imagenes
content_types_sms = ['text/plain',
]

# manejar tipos de extensiones campañas
content_types_img = ['image/png',
                     'image/jpeg',
]


# manejar tipos de docs permitidos por el portal
content_types_doc_perms = ['application/msword',
                           'application/pdf',
                           'application/excel',
                           'application/msword',    
                           'application/vnd.ms-excel'
]

USERNAME_MAXLENGTH = getattr(settings, 'USERNAME_MAXLENGTH', 75)
 
authhacks.hack_models(75)
authhacks.hack_forms(75)

class PorEstado(models.Model):
    estado = models.IntegerField(primary_key=True)
    nombre_estado = models.CharField(max_length=15)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)

    class Meta:
        db_table = 'por_estado'
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __unicode__(self):
        return self.nombre_estado


class PorPais(mixins.AuditMixin):
    nombre = models.CharField(max_length=32, primary_key=True)
    #nombre = models.CharField(max_length=32)
    
    class Meta:
        db_table = 'por_pais'
        verbose_name = 'Pais'
        verbose_name_plural = 'Paises'

    def __unicode__(self):
        return self.nombre


class PorProvincia(mixins.AuditMixin):
    nombre = models.CharField(max_length=32, primary_key=True)
    #nombre = models.CharField(max_length=32)
    pais = models.ForeignKey(PorPais, null=True, db_column='pais', blank=True)
    
    class Meta:
        db_table = 'por_provincia'
        verbose_name = 'Provincia'
        verbose_name_plural = 'Provincias'

    def __unicode__(self):
        return self.nombre

    def clean(self):
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not len(self.nombre) > 0:
                raise ValidationError('nombre no válido')


class PorCiudad(mixins.AuditMixin):
    nombre = models.CharField(max_length=32, primary_key=True)
    #nombre = models.CharField(max_length=32)
    provincia = models.ForeignKey(PorProvincia, null=True,
                                  db_column='provincia', blank=True)
    pais = models.ForeignKey(PorPais, null=True, db_column='pais', blank=True)
    
    class Meta:
        db_table = 'por_ciudad'
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'

    def __unicode__(self):
        return self.nombre

    def clean(self):
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not len(self.nombre) > 0:
                raise ValidationError('nombre no válido')


class PorEstadoNotificacion(models.Model):
    nombre = models.CharField(max_length=15, primary_key=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    estado = models.ForeignKey(PorEstado, null=True, db_column='estado',
                               blank=True)

    class Meta:
        db_table = 'por_estado_notificacion'
        permissions = (
            ("nuevo_porestadonotificacion", "Puede crear estado notificacion"),
            (
                "editar_porestadonotificacion",
                "Puede editar estado notificacion"),
            (
                "listar_porestadonotificacion",
                "Puede listar estado notificacion"),
        )

    def __unicode__(self):
        return self.nombre


class PorFuenteGeneracion(models.Model):
    nombre = models.CharField(max_length=15, primary_key=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    estado = models.ForeignKey(PorEstado, null=True, db_column='estado',
                               blank=True)

    class Meta:
        db_table = 'por_fuente_generacion'

    def __unicode__(self):
        return self.nombre


class Documento(models.Model):
    razon_social_emisor = models.CharField(max_length=300)
    ruc_emisor = models.CharField(max_length=13)
    clave_acceso = models.CharField(max_length=49, blank=True)
    numero_autorizacion = models.CharField(max_length=37)
    establecimiento = models.CharField(max_length=3)
    pto_emision = models.CharField(max_length=3)
    fecha_emision = models.DateField()
    direccion_establecimiento = models.CharField(max_length=300, blank=True)
    ciudad = models.ForeignKey(PorCiudad, null=True, db_column='ciudad',
                               blank=True)
    tipo_identificacion_receptor = models.CharField(max_length=2)
    identificacion_receptor = models.CharField(max_length=20)
    razon_social_receptor = models.CharField(max_length=300)
    monto_total = models.DecimalField(max_digits=14, decimal_places=2)
    moneda = models.CharField(max_length=15, blank=True)
    ruta_documento_xml = models.FileField(upload_to='uploads/xml')
    ruta_documento_pdf = models.FileField(upload_to='uploads/pdf')
    ruta_documento_otro = models.CharField(max_length=500, blank=True)
    aprobado_por = models.CharField(max_length=32, blank=True)
    observaciones = models.CharField(max_length=128, blank=True)
    estado_notificacion = models.ForeignKey(PorEstadoNotificacion, null=True,
                                            db_column='estado_notificacion',
                                            blank=True)
    
    fuente_generacion = models.ForeignKey(PorFuenteGeneracion, null=True,
                                          db_column='fuente_generacion',
                                          blank=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    estado = models.ForeignKey(PorEstado, null=True, db_column='estado', blank=True)
    secuencial = models.CharField(max_length=9, blank=True)
    tipo_comprobante = models.CharField(max_length=2, blank=True)
    leido = models.BooleanField()
    codigo_original = models.CharField(max_length=44)
    email_remitente = models.CharField(max_length=128)
    codigo_anulacion = models.CharField(max_length=87, blank=True)
    
    class Meta:
        db_table = 'documento'
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

        permissions = (
            ("listar_doc_rec", "Puede listar documentos recibidos"),
            ("listar_doc_emit", "Puede listar documentos emitidos"),
            ("listar_comp_cargados", "Puede listar comprobantes cargados"),
            ("reportes", "Reportes"),
        )

    def __unicode__(self):
        return self.razon_social_emisor


class DocumentoEmitido(Documento):
    class Meta:
        db_table = 'documento_emitido'
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos Emitidos'


class PorComprobanteRetencion(DocumentoEmitido):
    class Meta:
        db_table = 'por_comprobante_retencion'
        permissions = (
            ("nuevo_porcomprobanteretencion",
             "Puede crear comprobante retencion"),
            ("editar_porcomprobanteretencion",
             "Puede editar comprobant retencion"),
            ("listar_porcomprobanteretencion",
             "Puede listar comprobant retencion"),
        )
        verbose_name = 'Comprobante Rentencion'
        verbose_name_plural = 'Comprobantes Rentencion'


class PorTipoPersona(models.Model):
    nombre = models.CharField(max_length=15, primary_key=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    estado = models.ForeignKey(PorEstado, null=True, db_column='estado',
                               blank=True)

    def __unicode__(self):
        return self.nombre
    
    class Meta:
        db_table = 'por_tipo_persona'
        verbose_name = 'Tipo Persona'
        verbose_name_plural = 'Tipos Personas'


class PorFuenteRecepcion(models.Model):
    nombre = models.CharField(max_length=16, primary_key=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    estado = models.ForeignKey(PorEstado, null=True, db_column='estado',
                               blank=True)

    class Meta:
        db_table = 'por_fuente_recepcion'

    def __unicode__(self):
        return self.nombre


class PorTipoArchivo(models.Model):
    tipo = models.CharField(max_length=4, primary_key=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    estado = models.ForeignKey(PorEstado, null=True, db_column='estado',
                               blank=True)

    class Meta:
        db_table = 'por_tipo_archivo'

    def __unicode__(self):
        return self.tipo


class PorCategoria(mixins.AuditMixin):
    nombre = models.CharField(max_length=32, primary_key=True)
    
    class Meta:
        db_table = 'por_categoria'
        verbose_name = 'Categoria de Empresa'
        verbose_name_plural = 'Categorias de Empresas'

    def __unicode__(self):
        return self.nombre

    def clean(self):
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not len(self.nombre) > 0:
                raise ValidationError('nombre no válido')


class PorSubcategoria(mixins.AuditMixin):
    nombre = models.CharField(max_length=32, primary_key=True)
    categoria = models.ForeignKey(PorCategoria, null=True,
                                  db_column='categoria', blank=True)
    
    class Meta:
        db_table = 'por_subcategoria'
        verbose_name = 'Subcategoria de Empresas'
        verbose_name_plural = 'Subcategorias de Empresas'

    def __unicode__(self):
        return self.nombre

    def clean(self):
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not len(self.nombre) > 0:
                raise ValidationError('nombre no válido')

class PorTipoDirectorio(models.Model):
    nombre = models.CharField(max_length=32, choices=P.DIRECTORIOS_CHOICES,
                              default=P.DIRECTORIO_ENTRADA, primary_key=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    estado = models.ForeignKey(PorEstado, null=True, db_column='estado',
                               blank=True)

    class Meta:
        db_table = 'por_tipo_directorio'
        verbose_name = 'Tipo Directorio'
        verbose_name_plural = 'Tipos Directorio'

    def __unicode__(self):
        return self.nombre

    def clean(self):
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not len(self.nombre) > 0:
                raise ValidationError('nombre no válido')


class PorLog(mixins.AuditMixin):
    metodo = models.CharField(max_length=64, blank=True)
    objeto = models.CharField(max_length=256, blank=True)
    componente = models.CharField(max_length=16, blank=True)
    tipo = models.CharField(max_length=3, blank=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'por_log'


class PorNotaDebito(DocumentoEmitido):
    class Meta:
        db_table = 'por_nota_debito'
        permissions = (
            ("nuevo_pornotadebito", "Puede crear nota debito"),
            ("editar_pornotadebito", "Puede editar nota debito"),
            ("listar_pornotadebito", "Puede listar nota debito"),
        )


class PorGuiaRemision(DocumentoEmitido):
    class Meta:
        db_table = 'por_guia_remision'
        permissions = (
            ("nueva_porguiaremision", "Puede crear guia remision"),
            ("editar_porguiaremision", "Puede editar una guia remision"),
            ("listar_porguiaremision", "Puede listar guias remision"),
        )


class PorFactura(DocumentoEmitido):
    class Meta:
        db_table = 'por_factura'
        permissions = (
            ("nueva_porfactura", "Puede crear factura"),
            ("editar_porfactura", "Puede editar una factura"),
            ("listar_porfactura", "Puede listar facturas"),
        )


class PorNotaCredito(DocumentoEmitido):
    class Meta:
        db_table = 'por_nota_credito'
        permissions = (
            ("nuevo_pornotacredito", "Puede crear nota credito"),
            ("editar_pornotacredito", "Puede editar nota credito"),
            ("listar_pornotacredito", "Puede listar nota credito"),
        )


class PorTipoEmpresa(models.Model):
    nombre = models.CharField(max_length=32, primary_key=True)

    class Meta:
        db_table = 'por_tipo_empresa'

    def __unicode__(self):
        return self.nombre
    
class EmpresaSaveOnlyChangedFields(mixins.PorEmpresaMixin):

    es_exportador = models.BooleanField(default=False)
    reembolsos = models.BooleanField(default=False)

    def save(self, *args, **kw):
        if self.pk is not None:
            try:
                orig = PorEmpresa.objects.get(pk=self.pk)
                if orig.password_ftp != self.password_ftp:
                    if not self.password_ftp or self.password_ftp == '':
                        self.password_ftp = orig.password_ftp
                        #print 'EmpresaSaveOnlyChangedFields - Conservando valor', self.password_ftp
            except:
                pass
        super(EmpresaSaveOnlyChangedFields, self).save(*args, **kw)

    class Meta:
        abstract = True

class PorEmpresa(EmpresaSaveOnlyChangedFields):
    #datos generales emisor
    nombre_comercial = models.CharField(max_length=300)
    ruc = models.CharField(max_length=13, primary_key=True)
    razon_social = models.CharField(max_length=300)
    codigo_empresa = models.CharField(max_length=7)
    email_principal = models.CharField(max_length=256, blank=True)
    tipo = models.ForeignKey(PorTipoEmpresa, null=True, db_column='tipo',
                             blank=True)
    representante_legal = models.CharField(max_length=64, blank=True)
    server_name = models.CharField(max_length=16, blank=True)
    categoria_emisor = models.ForeignKey(PorCategoria, null=True,
                                         db_column='categoria_emisor',
                                         blank=True)
    subcategoria_emisor = models.ForeignKey(PorSubcategoria, null=True,
                                            db_column='subcategoria_emisor',
                                            blank=True)
    
    corporative_font_color = models.CharField(max_length=7, blank=True)
    corporative_background_color = models.CharField(max_length=7, blank=True)
    #datos ubicacion fisica emisor
    pais = models.ForeignKey(PorPais, null=True, db_column='pais', blank=True)
    provincia = models.ForeignKey(PorProvincia, null=True,
                                  db_column='provincia', blank=True)
    ciudad = models.ForeignKey(PorCiudad, null=True, db_column='ciudad',
                               blank=True)

    calle_principal = models.CharField(max_length=32, blank=True)
    calle_secundaria = models.CharField(max_length=32, blank=True)
    numeracion = models.CharField(max_length=8, blank=True)
    telefono_principal = models.CharField(max_length=12, blank=True)
    extension_principal = models.CharField(max_length=3, blank=True)
    telefono_secundario = models.CharField(max_length=12, blank=True)
    extension_secundaria = models.CharField(max_length=3, blank=True)
    direccion_matriz = models.CharField(max_length=300, blank=True)
    pagina_web = models.CharField(max_length=64, blank=True)
    email_secundario = models.CharField(max_length=256, blank=True)
    fax = models.CharField(max_length=12, blank=True)
    #datos perfil del emisor
    fecha_fundacion = models.DateField(null=True, blank=True)  #24
    mision = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    valores = models.TextField(blank=True)  #27

    fecha_inicio_contrato = models.DateField()
    fecha_fin_contrato = models.DateField()
    codigo_contribuyente_especial = models.CharField(max_length=5, blank=True)
    obligado_contabilidad = models.CharField(max_length=2,
                                             choices=P.SINO_CHOICES,
                                             default=P.SINO_SI, blank=True)
    sincronizado = models.BooleanField(default=False)
    perfil_facebook = models.CharField(max_length=128, blank=True)
    perfil_twitter = models.CharField(max_length=128, blank=True)
    perfil_linkedid = models.CharField(max_length=128, blank=True)
    perfil_googleplus = models.CharField(max_length=128, blank=True)
    logotipo = models.FileField(upload_to='uploads/empresa_logotipo')
    
    envio_sms = models.BooleanField(default=False)
    
    usuario_ftp = models.CharField(max_length=32, blank=True)    
    password_ftp = EncryptedField(blank=True)

    class Meta:
        db_table = 'por_empresa'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        permissions = (
            ("editar_perfil_empresa", "Puede editar perfil empresa"),
        )

    def __unicode__(self):
        return self.ruc


class PorOperadorPorCrear(models.Model):
    identificacion = models.CharField(max_length=20, primary_key=True, unique=True)
    nombres = models.CharField(max_length=64)
    apellidos = models.CharField(max_length=64)
    usuario = models.CharField(max_length=64)
    clave = models.CharField(max_length=32)
    creado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    email_secundario = models.CharField(max_length=64, null=True, blank=True)
    ruc_empresa = models.CharField(max_length=13, null=True, blank=True)
    estado = models.ForeignKey(PorEstado, null=True, db_column='estado',
                               blank=True)

    class Meta:
        db_table = 'por_operador_por_crear'
    
    def __unicode__(self):
        return self.identificacion


class PorOperador(mixins.AuditMixin):
    tipo_identificacion = models.CharField(max_length=2, choices=P.TIPOS_IDENTIFICACION_CHOICES, default=P.TID_CEDULA)
    identificacion = models.CharField(max_length=20, primary_key=True)
    nombres = models.CharField(max_length=64)
    apellidos = models.CharField(max_length=64)
    direccion = models.CharField(max_length=300, blank=True)
    telefono_principal = models.CharField(max_length=12, blank=True)
    telefono_secundario = models.CharField(max_length=12, blank=True)
    email_principal = models.CharField(max_length=64, blank=True)
    email_secundario = models.CharField(max_length=64, blank=True)
    ruc_empresa = models.ForeignKey(PorEmpresa, null=True, db_column='ruc_empresa',blank=True)
    user = models.ForeignKey(User, unique=True, db_column='user')

    sector = models.CharField(max_length=64, blank=True)
    codigo_postal = models.CharField(max_length=64, blank=True)
    perfil_facebook = models.CharField(max_length=256, blank=True)
    perfil_twitter = models.CharField(max_length=256, blank=True)
    perfil_linkedid = models.CharField(max_length=256, blank=True)
    perfil_googleplus = models.CharField(max_length=256, blank=True)
    titulo_profesional = models.CharField(max_length=64, blank=True)
    area_trabajo = models.CharField(max_length=64, blank=True)
    carrera = models.CharField(max_length=64, blank=True)
    lugar_estudio = models.CharField(max_length=64, blank=True)
    lugar_trabajo = models.CharField(max_length=64, blank=True)

    pregunta_1 = models.CharField(max_length=50, blank=True, choices=P.PREGUNTAS_PREDEFINIDAS_CHOICES)
    respuesta_1 = models.CharField(max_length=50, blank=True)
    pregunta_2 = models.CharField(max_length=50, blank=True)
    respuesta_2 = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'por_operador'
        permissions = (
            ("nuevo_poroperador", "Puede crear operador"),
            ("editar_poroperador", "Puede editar un operador"),
            ("listar_poroperador", "Puede listar operadores"),
        )
        verbose_name = 'Operador'
        verbose_name_plural = 'Operadores'

    def __unicode__(self):
        return u'%s, %s %s' % (self.identificacion,self.nombres, self.apellidos)


    def get_nombre_completo(self):
        name = []
        if self.nombres:
            name.append(self.nombres)
            name.append(' ')
        
        if self.apellidos:
            name.append(self.apellidos)
            
        return ''.join(name)
    
    def get_datos_empresariales(self):
        try:
            return PorDatosEmpresariales.objects.get(operador = self)
        except Exception as e:
            print 'get_datos_empresariales - Error', e
            return None
    

class PorOperadorForm(ModelForm):
    class Meta:
        model = PorOperador
        widgets = {
            'direccion': TextInput(attrs={'size': '15'}),
            'telefono_principal': TextInput(attrs={'size': '12'}),
            'telefono_secundario': TextInput(attrs={'size': '12'}),
            'email_principal': TextInput(attrs={'size': '17'}),
            'email_secundario': TextInput(attrs={'size': '17'}),
        }
        exclude = ('fecha_creacion',
                   'fecha_actualizacion', 'usuario_creacion',
                   'usuario_actualizacion', 'estado',
                   'ruc_empresa', 'user')


class PorTipoCliente(mixins.AuditMixin):
    nombre = models.CharField(max_length=15, primary_key=True)
    
    class Meta:
        db_table = 'por_tipo_cliente'


class PorDirectorioArchivosEmpresa(mixins.AuditMixin):
    ruta = models.CharField(max_length=500)
    tipo_directorio = models.ForeignKey(PorTipoDirectorio, null=True,
                                        db_column='tipo_directorio',
                                        blank=True)
    ruc_empresa = models.ForeignKey(PorEmpresa, null=True,
                                    db_column='ruc_empresa', blank=True)

    class Meta:
        db_table = 'por_directorio_archivos_empresa'
        verbose_name = 'Directorio'
        verbose_name_plural = 'Directorios'


#""" BUZON """


class DocumentoRecibido(Documento):
    class Meta:
        db_table = 'documento_recibido'


class BuzNotaDebito(DocumentoRecibido):
    class Meta:
        db_table = 'buz_nota_debito'
        permissions = (
            ("nuevo_buznotadebito", "Puede crear buz nota debito"),
            ("editar_buznotadebito", "Puede editar buz nota debito"),
            ("listar_buznotadebito", "Puede listar buz nota debito"),
        )


class BuzNotaCredito(DocumentoRecibido):
    class Meta:
        db_table = 'buz_nota_credito'
        permissions = (
            ("nuevo_buznotacredito", "Puede crear buz nota credito"),
            ("editar_buznotacredito", "Puede editar buz nota credito"),
            ("listar_buznotacredito", "Puede listar buz nota credito"),
        )


class BuzGuiaRemision(DocumentoRecibido):
    class Meta:
        db_table = 'buz_guia_remision'
        permissions = (
            ("nuevo_buzguiaremision", "Puede crear buz guia remision"),
            ("editar_buzguiaremision", "Puede editar buz guia remision"),
            ("listar_buzguiaremision", "Puede listar buz guia remision"),
        )


class BuzFactura(DocumentoRecibido):
    class Meta:
        db_table = 'buz_factura'
        permissions = (
            ("nuevo_buzfactura", "Puede crear buz factura"),
            ("editar_buzfactura", "Puede editar buz factura"),
            ("listar_buzfactura", "Puede listar buz factura"),
        )


class BuzComprobanteRetencion(DocumentoRecibido):
    class Meta:
        db_table = 'buz_comprobante_retencion'
        permissions = (
            ("nuevo_buzcomprobanteretencion", "Puede crear buz c retencion"),
            ("editar_buzcomprobanteretencion", "Puede editar buz c retencion"),
            ("listar_buzcomprobanteretencion", "Puede listar buz c retencion"),
        )


class BuzLog(models.Model):
    metodo = models.CharField(max_length=64, blank=True)
    objeto = models.CharField(max_length=256, blank=True)
    componente = models.CharField(max_length=16, blank=True)
    tipo = models.CharField(max_length=3, blank=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    id = models.IntegerField(primary_key=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    estado = models.ForeignKey(PorEstado, null=True, db_column='estado',
                               blank=True)

    class Meta:
        db_table = 'buz_log'


class BuzBuzon(mixins.AuditMixin):
    tipo_identificacion = models.CharField(max_length=2, blank=True)
    identificacion = models.CharField(max_length=20, blank=True)
    tipo_cliente = models.ForeignKey(PorTipoCliente, null=True,
                                     db_column='tipo_cliente', blank=True)
    tipo_persona = models.ForeignKey(PorTipoPersona, null=True,
                                     db_column='tipo_persona', blank=True)
    razon_social = models.CharField(max_length=200, blank=True)
    nombres = models.CharField(max_length=100, blank=True)
    apellidos = models.CharField(max_length=100, blank=True)
    email_buzon = models.CharField(max_length=200, blank=True)
    email_notificacion = models.CharField(max_length=200, blank=True)
    codigo_usuario = models.CharField(max_length=32, blank=True)
    password_usuario = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = 'buz_buzon'
        verbose_name = 'Buzon'
        verbose_name_plural = 'Buzon'

    def __unicode__(self):
        return self.razon_social

class BuzDocumento(mixins.AuditMixin):

    fecha_emision = models.DateField()
    tipo_comprobante = models.CharField(max_length=2, choices=P.TIPOS_DOCUMENTO)
    numero_comprobante = models.CharField(max_length=17, blank=True)
    categoria_emisor = models.ForeignKey(PorCategoria, null=True,
                                         db_column='categoria_emisor',
                                         blank=True)
    subcategoria_emisor = models.ForeignKey(PorSubcategoria, null=True,
                                            db_column='subcategoria_emisor',
                                            blank=True)
    monto_comprobante = models.DecimalField(max_digits=14, decimal_places=2)
    ciudad = models.ForeignKey(PorCiudad, null=True, db_column='ciudad',
                               blank=True)
    razon_social_emisor = models.CharField(max_length=300)
    ruc_emisor = models.CharField(max_length=13)
    establecimiento = models.CharField(max_length=3, blank=True)
    tipo_archivo = models.ForeignKey(PorTipoArchivo, null=True,
                                     db_column='tipo_archivo', blank=True)
    ruta_archivo = models.FileField(
        upload_to=lambda instance, filename:
        'uploads/documentos/{0}/{1}'.format(instance.buzon.identificacion,
                                            smart_str(filename)),
    )
    fuente_recepcion = models.ForeignKey(PorFuenteRecepcion, null=True,
                                         db_column='fuente_recepcion',
                                         blank=True)
    aprobado_por = models.CharField(max_length=32)
    numero_autorizacion = models.CharField(max_length=37)
    buzon = models.ForeignKey(BuzBuzon, null=True, db_column='buzon', blank=True)

    class Meta:
        db_table = 'buz_documento'


'''
------------------------------------
Modelos para Publicidad
------------------------------------
'''


class Cupon(mixins.CuponMixin):
    ruc_empresa = models.ForeignKey('PorEmpresa', db_column='ruc_empresa')
    titular_cupon = models.CharField(max_length=250)
    ruta_imagen_cupon = models.FileField(upload_to='uploads/cupones')
    codigos_ruta = ValidatedFileField(upload_to=lambda instance,
                filename: 'uploads/cupones/{0}/codigos/{1}'.format(instance.ruc_empresa, filename), max_upload_size=5000000)
    fecha_publicacion = models.DateTimeField()
    fecha_final_publicacion = models.DateTimeField()
    tipo_cupon = models.CharField(max_length=9)
    categoria = models.CharField(max_length=100, blank=True)
    sub_categoria = models.CharField(max_length=100)       
    redes_sociales = models.CharField(max_length=250, blank=True)
    detalles_cupon = models.CharField(max_length=250)
    detalles_validez = models.CharField(max_length=250)
    nro_impresiones = models.IntegerField(null=True, blank=True, default=0)
    nro_vistos = models.IntegerField(null=True, blank=True, default=0)

    class Meta:
        db_table = 'cupon'
        verbose_name = 'Cupon'
        verbose_name_plural = 'Cupones'
        permissions = (
            ("listar_cupones", "Puede listar cupones"),
        )

class CodigoCupon(mixins.AuditMixin):
    codigo = models.CharField(max_length=20)
    cupon = models.ForeignKey('Cupon', db_column='cupon_id')
    usos = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'codigo_cupon'
        verbose_name = 'Codigo de Cupon'
        verbose_name_plural = 'Codigos de Cupones'
        permissions = (
            ("listar_cods_cupones", "Puede listar codigos de cupones"),
        )

class Producto(mixins.CodeMixin):
    ruc_empresa = models.ForeignKey(PorEmpresa, db_column='ruc_empresa')
    titulo = models.CharField(max_length=100)
    imagen = ValidatedFileField(
        upload_to=lambda instance, filename:
        'uploads/productos/{0}/img/{1}'.format(instance.ruc_empresa,filename),
        max_upload_size=5000000,
        content_types=content_types_img
    )
    logotipo = ValidatedFileField(
        upload_to=lambda instance, filename:
        'uploads/productos/{0}/logotipos/{1}'.format(instance.ruc_empresa,filename),
        max_upload_size=5000000,
        content_types=content_types_img
    )
    fecha_publicacion = models.DateTimeField()
    #tiempo = models.CharField(max_length=250, blank=True)
    codigo_sku = models.CharField(max_length=100, blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    sub_categoria = models.CharField(max_length=100)    
    #redes_sociales = models.CharField(max_length=250, blank=True)
    detalles_producto = models.CharField(max_length=250, blank=True)
    url_compra = models.TextField(validators=[URLValidator()])
    nro_impresiones = models.IntegerField(null=True, blank=True, default=0)
    nro_vistos = models.IntegerField(null=True, blank=True, default=0)

    class Meta:
        db_table = u'producto'
        permissions = (
            ("listar_productos", "Puede listar productos"),
        )

    def __unicode__(self):
        return self.codigo_sku


class Banner(mixins.BannerMixin):
    id_banner = models.AutoField(primary_key=True)
    ruc_empresa = models.ForeignKey('PorEmpresa', db_column='ruc_empresa')
    nombre = models.CharField(max_length=250)
    posicion = models.CharField(max_length=50, blank=True)
    fecha_publicacion = models.DateTimeField()
    impresiones = models.IntegerField()
    impresiones_restantes = models.IntegerField(default=0)
    imagen = ValidatedFileField(upload_to=lambda instance,
        filename:'uploads/banners/{0}/{1}'.format(instance.ruc_empresa, filename), max_upload_size=5000000, content_types=content_types_img)
    url_banner_apunta = models.TextField(validators=[URLValidator()])
    nro_clicks = models.IntegerField(null=True, blank=True, default=0)

    def clean(self):
        if self.impresiones:
            if self.impresiones < 10:
                raise ValidationError('El numero de impresiones no puede ser menor a 10')

    class Meta:
        db_table = 'banner'
        permissions = (
            ("listar_banners", "Puede listar banners"),
        )


class CampaniaEmail(mixins.CampaingMixin):
    id_campania = models.AutoField(primary_key=True)
    ruc_empresa = models.ForeignKey('PorEmpresa', db_column='ruc_empresa')
    nombre = models.CharField(max_length=150)
    fecha_publicacion = models.DateTimeField()
    subject_email = models.CharField(max_length=200)
    banner_superior =  ValidatedFileField(upload_to=lambda instance, filename:
        'uploads/campania_email/{0}/banners/{1}'.format(instance.ruc_empresa, filename), max_upload_size=5000000, content_types=content_types_img)
    url_apunta_banner_superior = models.URLField()
    texto = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'campania_email'
        permissions = (
            ("listar_campania_email", "Puede listar campanias email"),
        )

post_save.connect(crear_campania_email, sender=CampaniaEmail)

class CampaniaSms(mixins.CampaingSMSMixin):
    id_campania_sms = models.AutoField(primary_key=True)
    ruc_empresa = models.ForeignKey('PorEmpresa', db_column='ruc_empresa')
    nombre = models.CharField(max_length=250)
    fecha_publicacion = models.DateTimeField()
    receptor_sms_archivo = ValidatedFileField(upload_to=lambda instance, filename:
        'uploads/campania_sms/{0}/{1}'.format(instance.ruc_empresa, filename), max_upload_size=5000000, content_types=content_types_sms)
    mensaje = models.CharField(max_length=140)
    nro_receptores = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'campania_sms'
        permissions = (
            ("listar_campania_sms", "Puede listar campanias sms"),
        )


post_save.connect(enviar_SMS_campania, sender=CampaniaSms)

        
'''

Publicidad: Categorizacion

'''
class CategoriaProducto(mixins.AuditMixin):
    nombre = models.CharField(max_length=32, primary_key=True)
    
    class Meta:
        db_table = 'categoria_producto'
        verbose_name = 'Categoria de Producto'
        verbose_name_plural = 'Categorias de Productos'

    def __unicode__(self):
        return self.nombre

    def clean(self):
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not len(self.nombre) > 0:
                raise ValidationError('nombre no válido')

class SubcategoriaProducto(mixins.AuditMixin):
    nombre = models.CharField(max_length=32, primary_key=True)
    categoria = models.ForeignKey(CategoriaProducto, null=True,
                                  db_column='categoria', blank=True)
    
    class Meta:
        db_table = 'subcategoria_producto'
        verbose_name = 'Subcategoria de Producto'
        verbose_name_plural = 'Subcategorias de Productos'

    def __unicode__(self):
        return self.nombre

    def clean(self):
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not len(self.nombre) > 0:
                raise ValidationError('nombre no válido')
            
'''
CONFIGURACIONES GENERALES
'''

class PorConfiguracion(mixins.AuditMixin):
    nombre = models.CharField(max_length=32,unique=True)
    valor = models.CharField(max_length=64, null=True)
    tipo = models.CharField(max_length=32, choices=P.TIPOS_DATOS_CHOICES,
                              default=P.TIP_DAT_STRING)   

    class Meta:
        db_table = 'por_configuracion'
        verbose_name = 'Configuracion General'
        verbose_name_plural = 'Configuraciones Generales'

    def __unicode__(self):
        return self.nombre

class PorDatosEmpresariales(mixins.AuditMixin):
    operador = models.ForeignKey('PorOperador', unique=True, db_column='identificacion_operador')
    ruc = models.CharField(max_length=13)
    razon_social = models.CharField(max_length=128)
    direccion_matriz = models.CharField(max_length=128)
    cargo = models.CharField(max_length=128)
    categoria = models.ForeignKey(PorCategoria, null=True, db_column='categoria', blank=True)
    telefono = models.CharField(max_length=13)
    telefono_celular = models.CharField(max_length=13)
    extension = models.CharField(max_length=6)
    email = models.CharField(max_length=128)
    ciudad = models.ForeignKey(PorCiudad, null=True, db_column='ciudad', blank=True)
    provincia = models.ForeignKey(PorProvincia, null=True, db_column='provincia', blank=True)
    pais = models.ForeignKey(PorPais, null=True, db_column='pais', blank=True)
    pagina_web = models.CharField(max_length=128)
    perfil_facebook = models.CharField(max_length=128, blank=True)
    perfil_twitter = models.CharField(max_length=128, blank=True)
    perfil_linkedid = models.CharField(max_length=128, blank=True)
    perfil_googleplus = models.CharField(max_length=128, blank=True)
    obligado_contabilidad = models.CharField(max_length=2, choices=P.SINO_CHOICES,blank=True)
    contribuyente_especial = models.CharField(max_length=2, choices=P.SINO_CHOICES,blank=True)
    usa_facturacion_electronica = models.CharField(max_length=2, choices=P.SINO_CHOICES,blank=True)
    
    class Meta:
        db_table = 'por_datos_empresariales'
        verbose_name = 'Datos Empresariales Operador'
        verbose_name_plural = 'Datos Empresariales Operador'
    
    def __unicode__(self):
        return self.operador.identificacion

class ImpdCatalogo(mixins.AuditMixin):
    descripcion = models.CharField(max_length=64)
    valor = models.CharField(max_length=16)
    tipo = models.CharField(max_length=8, choices = P.TIPOS_DATOS)
    modulo = models.CharField(max_length=16, choices = P.CATALOGOS)
    valor_dependencia = models.CharField(max_length=16, blank=True)
    modulo_dependencia = models.CharField(max_length=16, choices = P.CATALOGOS, blank=True)
    
    class Meta:
        db_table = 'impd_catalogo'
        verbose_name = 'Catalogo Imprenta Digital'
        verbose_name_plural = 'Catalogos Imprenta Digital'

class PorRucEspecial(mixins.AuditMixin):
    ruc = models.CharField(max_length=13)
    
    class Meta:
        db_table = 'por_ruc_especial'
        verbose_name = 'Ruc Especial'
        verbose_name_plural = 'Lista de RUCs Especiales'
