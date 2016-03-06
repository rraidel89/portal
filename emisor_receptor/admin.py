from django.contrib import admin

from core import models as core_models

class BannerAdmin(admin.ModelAdmin):
    list_display = ('id_banner', 'ruc_empresa', 'nombre', 'impresiones', 'impresiones_restantes',
                    'fecha_publicacion', 'fecha_actualizacion', 'estado', 'preview')
    list_filter = ('ruc_empresa',)
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion', 'estado' )
    
    def preview(self, obj):
        return '<a href="%s" target="blank"><img src="%s" width="50px" height="auto"></a>' % (obj.url_banner_apunta, obj.imagen.url)

    preview.short_description = 'Vista Previa'
    preview.allow_tags = True

admin.site.register(core_models.Banner, BannerAdmin)

class CuponAdmin(admin.ModelAdmin):
    list_display = ('id', 'ruc_empresa', 'titular_cupon', 'fecha_publicacion', 'nro_impresiones', 'nro_vistos',
                    'fecha_publicacion', 'fecha_actualizacion', 'estado')
    list_filter = ('ruc_empresa',)
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion', 'estado' )

admin.site.register(core_models.Cupon, CuponAdmin)

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'ruc_empresa', 'titulo', 'fecha_publicacion', 'codigo_sku', 'nro_vistos',
                    'categoria', 'sub_categoria','url_compra', 'fecha_actualizacion', 'estado')
    list_filter = ('ruc_empresa',)
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion', 'estado' )

admin.site.register(core_models.Producto, ProductoAdmin)

class CampaniaEmailAdmin(admin.ModelAdmin):
    list_display = ('id_campania', 'ruc_empresa', 'nombre',
                    'fecha_publicacion', 'subject_email', 'fecha_actualizacion', 'estado')
    list_filter = ('ruc_empresa',)
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion', 'estado' )

admin.site.register(core_models.CampaniaEmail, CampaniaEmailAdmin)

class CampaniaSmsAdmin(admin.ModelAdmin):
    list_display = ('id_campania_sms', 'ruc_empresa', 'nombre',
                    'fecha_publicacion', 'nro_receptores', 'fecha_actualizacion', 'estado')
    list_filter = ('ruc_empresa',)
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion', 'estado' )

admin.site.register(core_models.CampaniaSms, CampaniaSmsAdmin)

'''
GENERIC
'''

class PorEstadoAdmin(admin.ModelAdmin):
    list_display = ('estado', 'nombre_estado', 'fecha_actualizacion')
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion')

admin.site.register(core_models.PorEstado, PorEstadoAdmin)

class PorFuenteGeneracionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion')

admin.site.register(core_models.PorFuenteGeneracion, PorFuenteGeneracionAdmin)

class PorFuenteRecepcionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion')

admin.site.register(core_models.PorFuenteRecepcion, PorFuenteRecepcionAdmin)

class PorEstadoNotificacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion')

admin.site.register(core_models.PorEstadoNotificacion, PorEstadoNotificacionAdmin)

class PorTipoPersonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion')

admin.site.register(core_models.PorTipoPersona, PorTipoPersonaAdmin)

class PorLogAdmin(admin.ModelAdmin):
    list_display = ('metodo',  'componente', 'tipo', 'objeto', 'fecha_registro', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion')

admin.site.register(core_models.PorLog, PorLogAdmin)

class PorConfiguracionAdmin(admin.ModelAdmin):
    list_display = ('id',  'nombre', 'valor', 'tipo', 'fecha_creacion', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion')

admin.site.register(core_models.PorConfiguracion, PorConfiguracionAdmin)

class PorDatosEmpresarialesAdmin(admin.ModelAdmin):
    list_display = ('id',  'operador', 'ruc', 'razon_social', 'direccion_matriz', 'categoria', 'telefono', 'telefono_celular', 'extension', 'email', 'ciudad', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion')

admin.site.register(core_models.PorDatosEmpresariales, PorDatosEmpresarialesAdmin)

class ImpdCatalogoAdmin(admin.ModelAdmin):
    list_display = ('id', 'modulo', 'descripcion', 'valor', 'tipo', 'modulo_dependencia', 'valor_dependencia', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')

admin.site.register(core_models.ImpdCatalogo, ImpdCatalogoAdmin)

class PorRucEspecialAdmin(admin.ModelAdmin):
    list_display = ('id', 'ruc', 'usuario_creacion', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_actualizacion')

admin.site.register(core_models.PorRucEspecial, PorRucEspecialAdmin)
