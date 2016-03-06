# -*- coding: UTF-8 -*-
import datetime
from django.shortcuts import get_object_or_404
import sys

from innobee_util.os import get_lan_ip


__author__ = 'amarcillo'

import mailchimp

condiciones = {'field': 'interests', 'op': 'all', 'value': 'portal-innobee'}
hoy = datetime.datetime.now()
hoy = hoy.strftime('%Y-%m-%d')


def get_mailchimp_api():
    """valida la Key provista y retorna una instancia si es valida

    :return instancia válida de mailchimp:
    """
    m = mailchimp.Mailchimp('8f6715644ef149bf2a183c466e41a752-us8')
    try:
        m.helper.ping()
        return m
    except mailchimp.Error:
        print "Invalid API key"
        return None


def subscribir_usuario(email, grupo):
    """agrega un usuario a una lista y asignar el grupo por defecto
    :param email: e-mail del usuario a subscribir
    """
    email_key = {'email': email}
    m = get_mailchimp_api()
    lista = mailchimp.Lists(m)
    merge_vars = {'groupings': [{'id': 10897, 'groups': [grupo]}]}
    try:
        respuesta = lista.subscribe('25be04f5d4', email_key, merge_vars, None, True)
    except Exception as e:
        print 'Error - Ya esta subscrito', e
        merge_vars = {'groupings': [{'id': 10897, 'groups': [grupo]}]}
        respuesta = lista.update_member('25be04f5d4', email_key, merge_vars, None, True)
    print respuesta

def get_lista():
    """retorna la lista general al cual pertenencen todos los subscriptores
    """
    m = get_mailchimp_api()
    lista = mailchimp.Lists(m)
    return lista

def crear_segmento(nombre):
    """ crea un nuevo segmento, a los miembros de este segmento se enviaran
    los e-mails
    :param nombre: identificacion de la empresa
    """
    condicione = {'field': 'interests', 'op': 'all', 'value': nombre}
    lista = get_lista()
    respuesta = lista.segment_add('25be04f5d4', {'type': 'saved', 'name': nombre, 'segment_opts': {
                                                     'match': 'all','conditions': [condicione]}})

def crear_campania(id, nombre_empresa, ruc, text_content, fecha_publicacion,  img_banner, url_banner, subject_email):
    from core.models import CampaniaEmail

    m = get_mailchimp_api()
    campania = mailchimp.Campaigns(m)
    direccion = get_lan_ip()
    img_banner = img_banner[1:]

    condicione = {'field': 'interests', 'op': 'all', 'value': ruc}
    try:
        result_create_campania = campania.create('regular',
                {'list_id': '25be04f5d4',
                 'subject': subject_email,
                 'from_email': 'innobee.nimbus@gmail.com',
                 'from_name': 'Innobee - Facturación electrónica',
                 'to_name': 'Subscriptores Innobee Portal',
                 'template_id': 111625,
                 'title': 'campania---{0}---{1}'.format(nombre_empresa, hoy),
                 'tracking': {'opens': True, 'html_clicks': True, 'text_clicks': True}
                },
                {'sections': {
                    'banner_img': '<a target="_blank" href="{0}"><img src="http://{1}/{2}" /></a>'.format(
                        url_banner, direccion, img_banner),
                    'text_content':   text_content,
                },
                },
                {'match': 'all',
                 'conditions': [condicione]
                }
        , )
        print result
        cod_campania = result_create_campania.get('id', -1)
        print 'Campania Creada con Exito', cod_campania        
        CampaniaEmail.objects.filter(id_campania=id).update(codigo=cod_campania)
        campania.schedule(cod_campania, fecha_publicacion)        
    except:
        print 'Error al crear la campania: {0}'.format(result_create_campania)
        print result_create_campania

def editar_campania(cid, nombre_empresa, ruc, text_content, fecha_publicacion, img_banner, url_banner, subject_email):
    m = get_mailchimp_api()
    campania = mailchimp.Campaigns(m)
    direccion = get_lan_ip()
    img_banner = img_banner[1:]

    try:
        result = campania.update(cid, 'content',
            {'sections': {
                'banner_img': '<a target="_blank" href="{0}"><img src="http://{1}/{2}" /></a>'.format(url_banner, direccion, img_banner),
                'text_content': text_content,
            }})
    except:
        print ('Error al editar campania:', sys.exc_info()[0])
    try:
        result = campania.update(cid, 'options', {'list_id': '25be04f5d4',
                                              'subject': subject_email,
                                              'from_email': 'info@innobee.com',
                                              'from_name': 'Innobee - Facturación electrónica',
                                              'to_name': 'Subscriptores Innobee Portal',
                                              'template_id': 111625,
                                              'title': 'campania---{0}---{1}'.format(nombre_empresa, hoy),
                                              'tracking': {'opens': True, 'html_clicks': True, 'text_clicks': True}
        },)
        print result
        campania.schedule(cid, fecha_publicacion)
    except:
        print ('Error al editar campania:', sys.exc_info()[0])

    


def segment_exists(segmento):
    lista = get_lista()
    segmentos = lista.segments('25be04f5d4')
    for key, value in segmentos.iteritems():
        for item in value:
            if item['name'] == segmento:
                return True
    return False


def group_exists(nombre):
    lista = get_lista()
    grupos = lista.interest_groupings('25be04f5d4')
    for item in grupos:
        for value in item['groups']:
            if value['name'] == nombre:
                return True
    return False


def crear_grupo(nombre):
    lista = get_lista()
    print lista.interest_group_add('25be04f5d4', nombre)


def procesar_campania(created, id, ruc, nombre_empresa, text_content, fecha_publicacion, img_banner, url_banner, subject_email):
    from core.models import CampaniaEmail
    from imprenta_digital import models as impd_models
    
    clientes = impd_models.ImpdCliente.objects.filter(ruc_empresa=ruc)
    if not group_exists(ruc): crear_grupo(ruc)
    if not segment_exists(ruc): crear_segmento(ruc)

    for item in clientes:
        subscribir_usuario(item.email_principal, ruc)

    if created:
        crear_campania(id, nombre_empresa, ruc, text_content, fecha_publicacion, img_banner, url_banner, subject_email)
    else:
        obj = get_object_or_404(CampaniaEmail, pk=id)
        codigo = obj.codigo
        try:
            m = get_mailchimp_api()
            camp = mailchimp.Campaigns(m)
            camp.unschedule(codigo)
            editar_campania(codigo, nombre_empresa, ruc, text_content, fecha_publicacion, img_banner, url_banner, subject_email)
        except Exception as e:
            print 'procesar_campania - Error:',e

def get_grupos_usuario():
    lista = get_lista()
    lista.interest_groupings()


def reporte_campania(id_campania):
    from core.models import CampaniaEmail

    try:
        m = get_mailchimp_api()
        campania = CampaniaEmail.objects.filter(pk=id_campania)[:1].get()
        report = m.reports.summary(campania.codigo)
        return report
    except:
        return None
