#from emisor_receptor.views import sndemail
#from innobee_util.util import send_sms
from django.conf import settings
from innobee_portal import properties as P

from celery import task

import SOAPpy
import pysftp
import os

'''
@task()
def sms_sender(mensaje, receptores):
    send_sms(receptores, mensaje)
    # sndemail('alfredo', 'amarcillo@inprise.ec', 'pruebas')
'''

@task
def enviar_SMS_campania(sender, instance, created, **kwargs):
    from models import CampaniaSms
    from innobee_util.manejar_archivos import leer_desde_xls
    try:
        print 'enviar_SMS_campania - Obteniendo receptores de mensaje SMS...'
        fecha_publicacion = instance.fecha_publicacion
        archivo = instance.receptor_sms_archivo.url
        receptores_archivo = archivo.split('/', 1)[1]
        mensaje =  instance.mensaje
        print 'enviar_SMS_campania - Mensaje a enviar', mensaje
        receptores = leer_desde_xls(receptores_archivo)
        print 'enviar_SMS_campania - Encontrados', len(receptores), 'receptores'
        CampaniaSms.objects.filter(pk=instance.id_campania_sms).update(nro_receptores=len(receptores))
        #enviar_SMS.apply_async(args=[receptores, mensaje], eta=fecha_publicacion)
        enviar_SMS(receptores, mensaje)
    except Exception as e:
        print 'enviar_SMS - Error', e

@task
def enviar_SMS(receptores, mensaje):
    try:
        from django.conf import settings
        print 'enviar_SMS - Conectando WS PUBLIMES...'
        proxy = SOAPpy.SOAPProxy(settings.PUBLIMES_WS_URL, namespace = settings.PUBLIMES_WS_NAMESPACE,
                                 soapaction = settings.PUBLIMES_WS_CREATE_ACTION)
        
        namespace = settings.PUBLIMES_WS_NAMESPACE
        
        print 'enviar_SMS - Conectados!'
        proxy.config.debug = 1
        for numero_telefonico in receptores:
            
            print 'enviar_SMS - Enviando mensaje a', numero_telefonico
            resp = proxy.EnviarMensaje(SOAPpy.Types.untypedType(name = (namespace, "idCliente"), data = settings.PUBLIMES_WS_CLIENT),
                                        SOAPpy.Types.untypedType(name = (namespace, "contrasenia"), data = settings.PUBLIMES_WS_PWD),
                                        SOAPpy.Types.untypedType(name = (namespace, "operadora"), data = settings.PUBLIMES_WS_OPERADORA),
                                        SOAPpy.Types.untypedType(name = (namespace, "numeroTelefonico"), data = numero_telefonico),
                                        SOAPpy.Types.untypedType(name = (namespace, "mensaje"), data = mensaje))
            print 'enviar_SMS - Mensaje enviado!'
    except Exception as e:
        print 'enviar_SMS - Error', e


@task()
def subir_SFTP(empresa, file_path):
    print 'subir_SFTP - Conectando y subiendo...'
    host_addr = settings.SFTP_HOST
    if empresa.server_name == 'duke':
        host_addr = settings.SFTP_HOST_ARON
    elif empresa.server_name == 'dune':
        host_addr = settings.SFTP_HOST_ARGO
        
    with pysftp.Connection(host=host_addr, username=empresa.usuario_ftp, password=empresa.password_ftp) as sftp:
        with sftp.cd(get_directorio_entrada(empresa)):              # temporarily chdir to public
            sftp.put(file_path)  # upload file to public/ on remote
            print 'subir_SFTP - Archivo', file_path, 'subido con exito, removiendo...' 
            os.system('rm %s' % file_path)
            print 'subir_SFTP - Archivo', file_path, 'removido.' 
                
def get_directorio_entrada(empresa):
        directorios = empresa.pordirectorioarchivosempresa_set.filter(
            tipo_directorio__nombre=P.DIRECTORIO_ENTRADA)
        if directorios.count() > 0:
            return directorios[0].ruta
        return None
