# -*- encoding: utf-8 -*-
import datetime
import sys
from innobee_util.mail_chimp import procesar_campania
from innobee_util.manejar_archivos import leer_desde_xls

__author__ = 'amarcillo'


def send_sms_prog(sender, instance, created, **kwargs):
    from core.models import CampaniaSms
    # enviar sms programado a una hora
    from core.tasks import sms_sender

    fecha_publicacion = instance.fecha_publicacion
    receptores_archivo = instance.receptor_sms_archivo.url
    receptores_archivo = receptores_archivo.split('/', 1)[1]
    mensaje = instance.mensaje
    receptores = leer_desde_xls(receptores_archivo)
    nro_receptores = len(receptores)
    CampaniaSms.objects.filter(pk=instance.id_campania_sms).update(
        nro_receptores=nro_receptores)
    sms_sender.apply_async(args=[mensaje, receptores], eta=fecha_publicacion)
    print 'msj enviado'


def crear_campania_email(sender, instance, created, **kwargs):
    print 'crear_campania_email - Procesar campana para', instance.ruc_empresa
    empresa = instance.ruc_empresa
    fecha_publicacion = instance.fecha_publicacion
    img_banner = instance.banner_superior.url
    # +5 xq mailchimp  trabaja en horario gmt
    fecha_publicacion += datetime.timedelta(hours=10)
    fecha_publicacion = fecha_publicacion.strftime('%Y-%m-%d %H:%M:%S')    
    
    url_banner = instance.url_apunta_banner_superior
    
    #procesar_campania(created, instance.id_campania,empresa.ruc, empresa.nombre_comercial,unicode(instance.texto),fecha_publicacion,img_banner,url_banner,instance.subject_email)



