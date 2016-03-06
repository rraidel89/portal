from core import models as core_models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from innobee_portal import properties as P

from django.db.models.query_utils import Q

import datetime
import traceback

def get_configuration_value(name, valor=None, tipo=None):
    try:
        config = core_models.PorConfiguracion.objects.get(nombre = name)
        return config.valor
    except Exception as e:
        print 'No existe la variable de configuracion', nombre, e
        core_models.PorConfiguracion.objects.create(nombre = name, valor = valor, tipo = tipo)
    return None

def get_configuration_value_integer(name, valor=None, tipo=None):
    try:
        config = core_models.PorConfiguracion.objects.get(nombre = name)
        return int(config.valor)
    except Exception as e:
        print 'No existe la variable de configuracion', name, e
        core_models.PorConfiguracion.objects.create(nombre = name, valor = valor, tipo = tipo)
        return int(valor)
    return None

def check_user_has_incomplete_information(user):
    try:
        profile = user.get_profile()
        datos_empresariales = profile.get_datos_empresariales()
        max_days = get_configuration_value_integer('DIAS_POSTERIOR_REGISTRO', valor='5', tipo='Integer')
        hoy = datetime.datetime.now()
        fecha_registro_max = profile.fecha_creacion + datetime.timedelta(days=max_days)
        
        print 'check_user_has_incomplete_information Comparando', hoy, '>=', fecha_registro_max, 'and', profile.tipo_identificacion, 'and', profile.ruc_empresa is None
        if hoy >=  fecha_registro_max and profile.ruc_empresa is None and profile.tipo_identificacion == P.TID_RUC:
            if not datos_empresariales or not (datos_empresariales.telefono and datos_empresariales.direccion_matriz and \
                datos_empresariales.ruc and datos_empresariales.email and datos_empresariales.categoria and
                datos_empresariales.telefono_celular and \
                (datos_empresariales.perfil_facebook or datos_empresariales.perfil_twitter or \
                 datos_empresariales.perfil_linkedid or datos_empresariales.perfil_googleplus)):
                print 'check_user_has_incomplete_information - Reenviando a actualizacion de datos'
                return True
            else:
                print 'check_user_has_incomplete_information - NO CUMPLE SEGUNDA VALIDACION'
        else:
            print 'check_user_has_incomplete_information - NO CUMPLE PRIMERA VALIDACION'
    except Exception as e:
        print 'check_user_has_incomplete_information - Error inesperado', e
    return False

class FiltroHelper(object):
    
    def get_identificacion_usuario(self):
        identificacion = None
        try:
            perfil_usuario = self.request.user.get_profile()
            if perfil_usuario.ruc_empresa is not None:
                identificacion = perfil_usuario.ruc_empresa
            else:
                identificacion = perfil_usuario.identificacion
        except:
            pass
        return identificacion
        
    def get_dates_query(self, queries, start_date, end_date):
        fecha_desde, fecha_hasta = self.cleaned_data[start_date], self.cleaned_data[end_date]
        if fecha_desde and fecha_hasta: queries += [Q(fecha_emision__range=(fecha_desde, fecha_hasta))]
        elif fecha_desde and not fecha_hasta: queries += [Q(fecha_emision__gte=fecha_desde)]
        elif fecha_hasta and not fecha_desde: queries += [Q(fecha_emision__lte=fecha_hasta)]
        return queries
    
    def get_cdates_query(self, queries, start_date, end_date):
        fecha_desde, fecha_hasta = self.cleaned_data[start_date], self.cleaned_data[end_date]
        if fecha_desde and fecha_hasta: queries += [Q(fecha_publicacion__range=(fecha_desde, fecha_hasta))]
        elif fecha_desde and not fecha_hasta: queries += [Q(fecha_publicacion__gte=fecha_desde)]
        elif fecha_hasta and not fecha_desde: queries += [Q(fecha_publicacion__lte=fecha_hasta)]
        return queries
    
    def get_publish_dates_query(self, queries, start_date, end_date):
        fecha_desde, fecha_hasta = self.cleaned_data[start_date], self.cleaned_data[end_date]
        if fecha_desde and fecha_hasta: queries += [Q(fecha_publicacion__gte=fecha_desde) & Q(fecha_final_publicacion__lte=fecha_hasta)]
        elif fecha_desde and not fecha_hasta: queries += [Q(fecha_publicacion__gte=fecha_desde)]
        elif fecha_hasta and not fecha_desde: queries += [Q(fecha_final_publicacion__lte=fecha_hasta)]
        return queries
    
    def build_query(self, queries):
        query = None
        if queries and len(queries) > 0:
            query = queries.pop()
            for item in queries:
                query &= item
        return query
    
    def paginar(self, items):
        try:
            if self.request.GET.get(self.page_name): self.request.session[self.page_name] = self.request.GET.get(self.page_name)
            page_emit = int(self.request.session.get(self.page_name, 1))
        except ValueError:
            page_emit = 1
            self.request.session[self.page_name] = str(page_emit)
        
        paginador = Paginator(items, self.filas)
        try:
            items = paginador.page(page_emit)
        except PageNotAnInteger:
            items = paginador.page(1)
        except EmptyPage:
            items = paginador.page(paginador.num_pages)
        
        return items
        
class FiltroAjaxHelper(object):
        
    def return_ajax(self, dajax):
        try:
            dajax.script("hideWait();")
            json = dajax.json()
            return json
        except Exception as e:
            traceback.print_exc()
            
        return {}
    
    def get_ruc_empresa(self):
        return self.request.user.get_profile().ruc_empresa
