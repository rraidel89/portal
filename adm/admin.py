# -*- coding: UTF8 -*-
from django.forms.models import BaseInlineFormSet

from django.db import IntegrityError, transaction
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from django.template.loader import render_to_string
from django.conf.urls import patterns
from django.http import HttpResponseRedirect

from adm.models import DjangoMenu
from core.models import *
from innobee_portal import properties as P

from xml.etree import ElementTree as ET

from django.forms import widgets
import datetime
import traceback

class PorDirectorioArchivosEmpresaAdmin(admin.TabularInline):
    model = PorDirectorioArchivosEmpresa
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')

class PorEmpresaAdmin(admin.ModelAdmin):
    list_display = (
        'ruc', 'razon_social', 'categoria_emisor', 'email_principal', 'usuario_ftp', 'server_name', 'sincronizado', 'get_colors',
        'es_exportador', 'reembolsos')
    ordering = ('razon_social', )
    exclude = ['sincronizado', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_actualizacion', 'estado']
    inlines = [PorDirectorioArchivosEmpresaAdmin]
    search_fields = ['ruc', 'razon_social']

    def __init__(self, model, admin_site):
        super(PorEmpresaAdmin, self).__init__(model, admin_site)
        self.sincronizado = False
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'password_ftp':
          kwargs['widget'] = widgets.PasswordInput
        return super(PorEmpresaAdmin,self).formfield_for_dbfield(db_field,**kwargs)
    
    def get_colors(self, obj):
        return '<span style="color:%s;background:%s">%s</span>' % (obj.corporative_font_color,
                                                                   obj.corporative_background_color,
                                                                   obj.nombre_comercial)
    
    get_colors.short_description = 'Colores'
    get_colors.allow_tags = True
    
    
class PorCiudadAdmin(admin.ModelAdmin):
    list_display = ('nombre','fecha_actualizacion', 'estado')
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion', 'estado' )

class PorProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pais','fecha_actualizacion', 'estado' )
    #list_filter = ('pais', )
    #ordering = ('pais', 'nombre', )
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion', 'estado' )

class PorPaisAdmin(admin.ModelAdmin):
    list_display = ('nombre','fecha_actualizacion', 'estado')
    #ordering = ('nombre',)
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion', 'estado' )

class BuzBuzonAdmin(admin.ModelAdmin):
    list_display = (
        'tipo_identificacion', 'identificacion', 'razon_social', 'email_buzon', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ['identificacion', 'razon_social']

class PorOperadorAdmin(admin.ModelAdmin):
    list_display = ('tipo_identificacion', 'identificacion', 'nombres', 'apellidos', 'email_principal', 'ruc_empresa', 'user')
    raw_id_fields = ("ruc_empresa",)

class PorOperadorPorCrearAdmin(admin.ModelAdmin):
    list_display = ('identificacion', 'nombres', 'apellidos', 'usuario', 'creado', 'ruc_empresa')
    search_fields = ['identificacion', 'nombres', 'apellidos']

class RequiredInlineFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super(RequiredInlineFormSet, self)._construct_form(i, **kwargs)
        form.empty_permitted = False
        return form

class UserProfileInline(admin.StackedInline):
    model = PorOperador
    fk_name = 'user'
    extra = 1
    max_num = 1
    raw_id_fields = ('ruc_empresa',)
    formset = RequiredInlineFormSet
    exclude = ('fecha_actualizacion', 'fecha_creacion', 'usuario_creacion', 'usuario_actualizacion', 'estado' )

class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'is_active')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(DjangoMenu)
admin.site.register(PorOperador, PorOperadorAdmin)
admin.site.register(PorOperadorPorCrear, PorOperadorPorCrearAdmin)
admin.site.register(PorEmpresa, PorEmpresaAdmin)
admin.site.register(PorCiudad, PorCiudadAdmin)
admin.site.register(PorProvincia, PorProvinciaAdmin)
admin.site.register(PorPais, PorPaisAdmin)
admin.site.register(PorTipoDirectorio)
admin.site.register(BuzBuzon, BuzBuzonAdmin)

class SubCategoriaProductoAdmin(admin.TabularInline):
    model = SubcategoriaProducto
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_actualizacion', 'estado')
    max_num = 50

class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_actualizacion', 'estado')
    inlines = [SubCategoriaProductoAdmin, ]

admin.site.register(CategoriaProducto, CategoriaProductoAdmin)

class PorSubcategoriaAdmin(admin.TabularInline):
    model = PorSubcategoria
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_actualizacion', 'estado')
    max_num = 50

class PorCategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_actualizacion', 'estado')
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    inlines = [PorSubcategoriaAdmin, ]

admin.site.register(PorCategoria, PorCategoriaAdmin)

class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('razon_social_emisor', 'ruc_emisor', 'clave_acceso', 'numero_autorizacion', 'codigo_original', 'fecha_emision',
                    'identificacion_receptor', 'razon_social_receptor', 'monto_total', 'estado_notificacion', 'fuente_generacion',
                    'usuario_actualizacion','fecha_actualizacion','estado')
    exclude = ('fecha_creacion', 'fecha_actualizacion', 'usuario_creacion',
               'usuario_actualizacion', 'estado')
    list_filter = ('ruc_emisor', 'estado_notificacion', 'fuente_generacion', 'fecha_emision')
    ordering = ('ruc_emisor', 'identificacion_receptor',)
    search_fields = ['codigo_original', 'identificacion_receptor', 'clave_acceso']

admin.site.register(Documento, DocumentoAdmin)
