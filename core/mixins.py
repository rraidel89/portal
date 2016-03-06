# -*- coding: utf-8 -*-
from django.db import models, IntegrityError, transaction
from django.utils import timezone
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_unicode
from django.contrib.auth.models import User
from django.conf import settings
from innobee_portal import properties as P

import hashlib
import datetime
from generators import RandomCodes, CuponCodesGenerator

def get_active_status():
    if not hasattr(get_active_status, "active_status"):
        import models as core_models
        try:
            estado = core_models.PorEstado.objects.get(nombre_estado = P.ACTIVE_STATUS)
        except:
            return None
        get_active_status.active_status = estado
    return get_active_status.active_status

def get_inactive_status():
    if not hasattr(get_inactive_status, "inactive_status"):
        import models as core_models
        try:
            estado = core_models.PorEstado.objects.get(nombre_estado = P.INACTIVE_STATUS)
        except:
            return None
        get_inactive_status.inactive_status = estado
    return get_inactive_status.inactive_status

def get_anulado_status():
    if not hasattr(get_anulado_status, "anulado_status"):
        import models as core_models
        try:
            estado = core_models.PorEstado.objects.get(nombre_estado=P.ANULADO_STATUS)
        except:
            estado = core_models.PorEstado()
            estado.estado = 5
            estado.nombre_estado = P.ANULADO_STATUS
            estado.fecha_creacion = timezone.now()
            estado.fecha_actualizacion = timezone.now()
            estado.usuario_creacion = 'root'
            estado.usuario_actualizacion = 'root'
            estado.save()
        get_anulado_status.anulado_status = estado
    return get_anulado_status.anulado_status

def get_rejected_notif_status():
    if not hasattr(get_rejected_notif_status, "rejected_notif_status"):
        import models as core_models
        try:
            estado = core_models.PorEstadoNotificacion.objects.get(nombre = P.NOTIF_REJECTED_STATUS)
        except Exception as e:
            print 'get_rejected_notif_status - Error', e
        get_rejected_notif_status.rejected_notif_status = estado
    return get_rejected_notif_status.rejected_notif_status

def get_authorized_notif_status():
    if not hasattr(get_authorized_notif_status, "authorized_notif_status"):
        import models as core_models
        try:
            estado = core_models.PorEstadoNotificacion.objects.get(nombre = P.NOTIF_AUTHORIZED_STATUS)
        except Exception as e:
            print 'get_authorized_notif_status - Error', e
        get_authorized_notif_status.authorized_notif_status = estado
    return get_authorized_notif_status.authorized_notif_status

def get_onoff_status():
    if not hasattr(get_onoff_status, "onoff_status"):
        import models as core_models
        try:
            estados = core_models.PorEstado.objects.filter(Q(nombre_estado__icontains = P.ACTIVE_STATUS) | Q(nombre_estado__icontains = P.INACTIVE_STATUS))
        except Exception as e:
            print 'get_onoff_status - Error', e
            return None
        get_onoff_status.onoff_status = estados
    return get_onoff_status.onoff_status

def get_notify_status():
    if not hasattr(get_notify_status, "notify_status"):
        import models as core_models
        try:
            estados = core_models.PorEstadoNotificacion.objects.filter(estado = get_active_status())
        except Exception as e:
            print 'get_notify_status - Error', e
            return None
        get_notify_status.notify_status = estados
    return get_notify_status.notify_status

def get_categorias_producto():
    if settings.VERSION_FINAL:
        if not hasattr(get_categorias_producto, "categorias"):
            import models as core_models
            try:
                categorias = core_models.CategoriaProducto.objects.filter(estado = get_active_status())
            except Exception as e:
                print 'get_categorias_producto - Error', e
                return None
            get_categorias_producto.categorias = categorias
        return get_categorias_producto.categorias
    import models as core_models
    return core_models.CategoriaProducto.objects.all()

def get_subcategorias_producto():
    if settings.VERSION_FINAL:
        if not hasattr(get_subcategorias_producto, "subcategorias"):
            import models as core_models
            try:
                subcategorias = core_models.SubcategoriaProducto.objects.filter(estado = get_active_status())
            except Exception as e:
                print 'get_subcategorias_producto - Error', e
                return None
            get_subcategorias_producto.subcategorias = subcategorias
        return get_subcategorias_producto.subcategorias
    import models as core_models
    return core_models.SubcategoriaProducto.objects.all()

def get_categorias_empresa():
    if settings.VERSION_FINAL:
        if not hasattr(get_categorias_empresa, "categorias"):
            import models as core_models
            try:
                categorias = core_models.PorCategoria.objects.filter(estado = get_active_status())
            except Exception as e:
                print 'get_categorias_empresa - Error', e
                return None
            get_categorias_empresa.categorias = categorias
        return get_categorias_empresa.categorias
    import models as core_models
    return core_models.PorCategoria.objects.filter(estado = get_active_status())

def get_subcategorias_empresa():
    if settings.VERSION_FINAL:
        if not hasattr(get_subcategorias_empresa, "subcategorias"):
            import models as core_models
            try:
                subcategorias = core_models.PorSubcategoria.objects.filter(estado = get_active_status())
            except Exception as e:
                print 'get_subcategorias_empresa - Error', e
                return None
            get_subcategorias_empresa.subcategorias = subcategorias
        return get_subcategorias_empresa.subcategorias
    import models as core_models
    return core_models.PorSubcategoria.objects.filter(estado = get_active_status())

def get_paises():
    if settings.VERSION_FINAL:
        if not hasattr(get_paises, "paises"):
            import models as core_models
            try:
                paises = core_models.PorPais.objects.filter(estado = get_active_status())
            except Exception as e:
                print 'get_ciudades - Error', e
                return None
            get_paises.paises = paises
        return get_paises.paises
    import models as core_models
    return core_models.PorPais.objects.filter(estado = get_active_status())

def get_provincias():
    if settings.VERSION_FINAL:
        if not hasattr(get_provincias, "provincias"):
            import models as core_models
            try:
                provincias = core_models.PorProvincia.objects.filter(estado = get_active_status())
            except Exception as e:
                print 'get_ciudades - Error', e
                return None
            get_provincias.provincias = provincias
        return get_provincias.provincias
    import models as core_models
    return core_models.PorProvincia.objects.filter(estado = get_active_status())

def get_ciudades():
    if settings.VERSION_FINAL:
        if not hasattr(get_ciudades, "ciudades"):
            import models as core_models
            try:
                ciudades = core_models.PorCiudad.objects.filter(estado = get_active_status())
            except Exception as e:
                print 'get_ciudades - Error', e
                return None
            get_ciudades.ciudades = ciudades
        return get_ciudades.ciudades
    import models as core_models
    return core_models.PorCiudad.objects.filter(estado = get_active_status())


class AuditMixin(models.Model):
    """
    Mixin de Auditoria
    """
    
    """
    Campos de Auditoria Comunes
    """
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=32)
    usuario_actualizacion = models.CharField(max_length=32)
    estado = models.ForeignKey('PorEstado', null=True, db_column='estado',
                               blank=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        print 'SAVING...'   
        if not self.pk or not self.estado:
            self.estado = get_active_status()
            
        if not self.pk or not self.usuario_creacion or not not self.fecha_creacion:
            if not self.fecha_creacion:
                self.fecha_creacion = timezone.now()

            if not self.usuario_creacion and user:
                if isinstance(user, User): user = user.username[:32]
                if user: self.usuario_creacion = user[:32]
        
        self.fecha_actualizacion = timezone.now()
        
        if user:
            if isinstance(user, User): user = user.username[:32]
            self.usuario_actualizacion = user[:32]
        
        obj = super(AuditMixin, self).save(*args, **kwargs)
        return obj

    class Meta:
        abstract = True
        
class IMPDComprobanteMixin(AuditMixin):
    
    id_configuracion = models.ForeignKey('ImpdFacturaConfiguracion', db_column='id_configuracion')
    codigo_original = models.CharField(max_length=44)
    secuencial = models.CharField(max_length=9, blank=True)
    
    def get_secuencial(self):
        return '%s-%s-%s' % (self.id_configuracion.establecimiento, self.id_configuracion.punto_emision, self.secuencial)
    
    def check_autorizado(self):
        from core import models as core_models
        if self.codigo_original:
            codigo_inicial = self.codigo_original[:30]
            #print 'codigo_inicial',codigo_inicial
            docs = core_models.Documento.objects.filter(codigo_original__istartswith = codigo_inicial)
            return docs.count() > 0
        return False

    def check_activo(self):
        return self.estado == get_active_status()
    
    class Meta:
        abstract = True

class PorEmpresaMixin(AuditMixin):
    """
    Mixin de Empresa
    """
   
    def save(self, *args, **kwargs):
        self.sincronizado = False
        obj = super(PorEmpresaMixin, self).save(*args, **kwargs)
        return obj

    class Meta:
        abstract = True

class CodeMixin(AuditMixin):
    """
    Mixin de Codigos
    """
    codigo = models.CharField(max_length=15, unique=True)
   
    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = RandomCodes.id_generator(size=10)
            super(CodeMixin, self).save(*args, **kwargs)
            if self.pk:
                self.codigo = ''.join( [ RandomCodes.id_generator(size=8), str(self.pk).zfill(7)[:7] ] )
        obj = super(CodeMixin, self).save(*args, **kwargs)
        return obj

    class Meta:
        abstract = True
        
class CampaingMixin(AuditMixin):
    """
    Mixin de Codigos
    """
   
    def save(self, *args, **kwargs):
        self.fecha_publicacion = datetime.datetime.combine(self.fecha_publicacion, datetime.datetime.now().time())
        obj = super(CampaingMixin, self).save(*args, **kwargs)
        return obj

    class Meta:
        abstract = True
        
class CampaingSMSMixin(AuditMixin):
    """
    Mixin de Codigos
    """
   
    def save(self, *args, **kwargs):
        obj = super(CampaingSMSMixin, self).save(*args, **kwargs)
        return obj

    class Meta:
        abstract = True
        
class CuponMixin(CodeMixin):
    """
    Mixin de Cupon
    """
   
    def save(self, *args, **kwargs):
        if CuponCodesGenerator.verifyCuponCodesEmpty(self):
            print 'CuponMixin.save - El cupon no tiene codigos almacenados, procedemos a crearlos.'
            super(CuponMixin, self).save(*args, **kwargs)
            return CuponCodesGenerator.readAndCreateCodes(self)
        return super(CuponMixin, self).save(*args, **kwargs)

    def get_coupon_code(self):
        return CuponCodesGenerator.getRandomCode(self)

    class Meta:
        abstract = True
        
class BannerMixin(AuditMixin):
    """
    Mixin de Banner
    """
   
    def save(self, *args, **kwargs):
        if not hasattr(self,'impresiones_restantes') or self.impresiones_restantes is None or self.pk is None:
            if self.impresiones:
                self.impresiones_restantes = self.impresiones
            else:
                self.impresiones_restantes = 1
        if not hasattr(self,'nro_clicks') or self.nro_clicks is None or self.pk is None:
            self.nro_clicks = 0
        return super(BannerMixin, self).save(*args, **kwargs)

    class Meta:
        abstract = True

