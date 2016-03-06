#
# Aqui defino mis contexts procesor para obtener en los templates objetos
# por defecto
#
#
from django.contrib.auth.models import Group
import user
from django.db.models import Count
from django.db.models.query_utils import Q

import re

from adm.models import DjangoMenu
from core.models import Documento, PorEmpresa
from innobee_portal import properties as P

from django.conf import settings

from django.db import connection

def context(request):
    context_default = {}
    connection._rollback()
    if request.user.is_authenticated():
        #Objeto usuario
        if hasattr(request, 'user'):
            try:
                perfil_usuario = request.user.get_profile()
    
                if perfil_usuario.ruc_empresa is not None:
                    ruc_empresa = perfil_usuario.ruc_empresa
                    empresa = PorEmpresa.objects.filter(pk=ruc_empresa)[:1].get()
                    context_default['razon_social_empresa'] = empresa.razon_social
                else:
                    context_default['razon_social_empresa'] = None
            except:
                pass
            
            try:
                # grupo al cual pertenece el usuario
                groups = request.user.groups.all()
                grupo = None
                if groups.count() > 0:
                    grupo = request.user.groups.all()[0].name
                else:
                    try:
                        grupo = Group.objects.get(name=P.GRUPO_DEFAULT)
                    except:
                        try:
                            grupo = Group.objects.create(name=P.GRUPO_DEFAULT)
                        except Exception as ex:                    
                            print ex
                    
                    try:
                        if grupo:
                            grupo.user_set.add(request.user)
                            grupo.save()
                    except Exception as ex:                    
                        print ex
    
                context_default['grupo'] = grupo
            except Exception as gex:
                context_default['grupo'] = None
                print gex
                
        try:
            #Coleccion de objetos menu de nivel 0
            print 'TRAYENDO MENUS...'
            if True: # not ('menus1' in request.session and 'menus2' in request.session):
                try:
                    menu_1 = DjangoMenu.objects.get(name='Menu1')
                except Exception as e:
                    menu_1 = None
                    print 'ERROR MENU 1: ', e
                
                try:
                    menu_2 = DjangoMenu.objects.get(name='Menu2')
                except Exception as e:
                    menu_2 = None
                    print 'ERROR MENU 2: ', e
                
                if menu_1:
                    request.session['menus1'] = DjangoMenu.objects.select_related().filter(
                                                    level=0, parent=menu_1.pk, visible=True,
                                                    is_active=True).order_by('index')
                else:
                    print 'NO HAY MENUS 1'
                    request.session['menus1'] = []
                
                if menu_2:
                    request.session['menus2'] = DjangoMenu.objects.select_related().filter(
                                                parent=menu_2.pk, visible=True,
                                                is_active=True).order_by('index')
                else:
                    print 'NO HAY MENUS 2'
                    request.session['menus2'] = []
            else:
                print 'MENUS EN SESION'
                
            context_default['menus1'] = request.session['menus1']
            context_default['menus2'] = request.session['menus2']
        except Exception as mex:
            context_default['menus1'] = None
            context_default['menus2'] = None
            print 'ERROR AL TRAER MENUS', mex
        
        if request.user.is_authenticated():
            context_default['esta_logueado'] = 'ok'

        path = request.get_full_path()
        context_default['full_path'] = re.sub(r'\?.*$', "", path)

        try:
            update_current_menus(context_default['menus1'], context_default['menus2'],
                                 context_default['full_path'])
        except Exception as uex:
            print uex
        
    empresa_usuario = ''   
    try:
        perfil_usuario = request.user.get_profile()
        if perfil_usuario.ruc_empresa is not None:
            empresa_usuario = PorEmpresa.objects.get(ruc=perfil_usuario.ruc_empresa)
        context_default['logotipo_empresa'] = empresa_usuario
    except:
        pass    
    
    context = {'DOMAIN_INNOBEE': settings.DOMAIN_INNOBEE}
    return context_default


def update_current_menus(menus1, menus2, full_path):
    for m in menus1:
        m.is_selected = False
        for c in m.childrens:
            c.is_selected = False
            if c.url == full_path:
                m.is_selected = True
                c.is_selected = True

    for m2 in menus2:
        m2.is_selected = False
        for c2 in m2.childrens:
            c2.is_selected = False
            if c2.url == full_path:
                m2.is_selected = True
                c2.is_selected = True


def notificaciones(request):
    if request.user.is_authenticated():
        try:
            perfil_usuario = request.user.get_profile()
            if perfil_usuario.ruc_empresa is not None:
                queries_notificacion = [
                Q(identificacion_receptor=perfil_usuario.ruc_empresa)]
            else:
                queries_notificacion = \
                    [Q(identificacion_receptor=perfil_usuario.identificacion)]

            query_notificacion = queries_notificacion.pop()
            for item in queries_notificacion:
                query_notificacion &= item
    
            get_logo = 'SELECT logotipo from por_empresa WHERE ' \
                       'por_empresa.ruc=documento.ruc_emisor'
    
            print 'QUERY NOTIFICACIONES', query_notificacion
    
            notificaciones = Documento.objects.filter(query_notificacion)
            
            print 'NOTIFICACIONES A', len(notificaciones)
    
            notificaciones = notificaciones.filter(Q(leido=False) | Q(leido__isnull=True))
    
            print 'NOTIFICACIONES B', len(notificaciones)
    
            notificaciones = notificaciones.extra(select={'logotipo': get_logo}).\
                order_by('-fecha_creacion')
        
            notificaciones = notificaciones.values('id','razon_social_emisor','logotipo', 'fecha_actualizacion', 'tipo_comprobante').distinct()
        
            limit_by = 5
            if len(notificaciones) <= 5:
                limit_by = len(notificaciones)
    
            print 'Preparando ', len(notificaciones), 'Notificaciones'
    
            #nro_notificaciones = Documento.objects.filter(query_notificacion).exclude(leido=True).\
            #    annotate(count=Count('pk'))
    
            return {'notificaciones': notificaciones[:limit_by],
                    'nro_notificaciones': len(notificaciones),
                    }
        except:
            pass
    
    return {}
