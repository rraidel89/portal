from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.views.generic.base import View

from wkhtmltopdf.views import PDFTemplateResponse

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone

from core.models import Cupon, Producto
from core import models as core_models
from core import mixins as core_mixins

from django.db.models import Q

import datetime
from django.template.loader import render_to_string

__author__ = 'diego'

class CuponPDF(View):
    template = 'emisores/cupon-pdf.html'

    def get(self, request, *args, **kwargs):
        response = PDFTemplateResponse(request=request,
                                       template=self.template,
                                       filename="cupon-descuento.pdf",
                                       context=self.get_context_data(),
                                       show_content_in_browser=False,
                                       cmd_options={'margin-top': 10},
        )
        return response

    def get_context_data(self):
        return {
            "form_cupon": self.get_object(),
        }

    def get_object(self):
        return get_object_or_404(Cupon, pk=self.kwargs.get("id_cupon"))


class ProductoPDF(View):
    template = 'emisores/producto-pdf.html'

    def get(self, request, *args, **kwargs):
        response = PDFTemplateResponse(request=request,
                                       template=self.template,
                                       filename="producto.pdf",
                                       context=self.get_context_data(),
                                       show_content_in_browser=False,
                                       cmd_options={'margin-top': 10},
        )
        return response

    def get_context_data(self):
        return {
            "form": self.get_object(),
        }

    def get_object(self):
        return get_object_or_404(Producto, pk=self.kwargs.get("id_prod"))


class LoggedInMixin(object):
    """clase auxilar utilizada en las cbv para
     determinar si usuario esta logueado"""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoggedInMixin, self).dispatch(*args, **kwargs)


def send_sms(receptores, mensaje):
    from clickatell.api import Clickatell

    for receptor in receptores:
        receiver = str(receptor)
        print receiver
        clickatell = Clickatell('multipasajes', 'UgSfVKWNKJgHNJ', '3449865')
        [resp] = clickatell.sendmsg(recipients=[receiver],
                                    # sender='0969199749',
                                    text=mensaje)
        print resp


def sndemail(user, email, comentario, emisor, monto, numero):
    # Enviar el archivo por mail
    from django.core.mail import EmailMessage

    if not numero:
        numero = '---'
    try:
        email = EmailMessage('INNOBEE FACTURACION - COMPROBANTE RECHAZADO',
                             '''
                             Se ha rechazado el comprobante:
                             USUARIO:               %s
                             COMENTARIO:            %s
                             EMISOR:                %s
                             NUMERO DE COMPROBANTE: %s
                             MONTO:                 %s

                             ========================================'''
                             % (user, comentario, emisor, numero, monto),
                             to=[email])
        email.send()
        print 'msj enviado'
    except Exception as e:
        print("Error al enviar el e-mail: {0}".format(e) ) #sys.exc_info()[0]
        add_log_error('innobee-util.sndemail', "{0}".format(e))
    return ''

def enviar_email_rechazo_comprobante(user, email, comentario, emisor, monto, numero):
    # Enviar el archivo por mail
    from django.core.mail import EmailMessage

    if not numero: numero = '---'
    if not monto: monto = '---'
    
    try:
        print 'enviar_email_rechazo_comprobante - Enviando a %s...' % email
        email = EmailMessage(subject='Comprobante Rechazado por Usuario en Innobee',
                             body='''
                             Se ha rechazado el Comprobante siguiente:
                             USUARIO:                   %s
                             COMENTARIO:                %s
                             EMISOR:                    %s
                             NUMERO DE COMPROBANTE:     %s
                             MONTO:                     %s

                             Dicho comprobante fue enviado por esta cuenta de correo o por la Empresa a la que pertenece.'''
                             % (user, comentario, emisor, numero, monto),
                             to=[email], from_email='info@innobeefactura.com')
        email.send()
        print 'enviar_email_rechazo_comprobante - Enviado exitosamente a %s' % email
    except Exception as e:
        print("Error al enviar el e-mail: {0}".format(e) )
        add_log_error('innobee-util.sndemail', "{0}".format(e))
    return ''

def enviar_email_notificacion(emails, documento, empresa):
    # Enviar el archivo por mail
    from django.core.mail import EmailMultiAlternatives

    try:
        server_name = empresa.server_name or 'innobee'
        if server_name=='duke': server_name = 'aron'
        elif server_name=='dune': server_name = 'argo'
        auth_path = '/home/sysadmin/%s-docs/%s/autorizados/%s' % (server_name, empresa.ruc, documento.codigo_original)
        template = '/home/sysadmin/%s-docs/email-info-template.ftl' % server_name

        tipo_documento = ''
        if documento.tipo_comprobante == 'FE':
            tipo_documento = 'una FACTURA'
        elif documento.tipo_comprobante == 'CR':
            tipo_documento = 'un COMPROBANTE DE RETENCION'
        elif documento.tipo_comprobante == 'NC':
            tipo_documento = 'una NOTA DE CREDITO'
        elif documento.tipo_comprobante == 'ND':
            tipo_documento = 'una NOTA DE DEBITO'
        elif documento.tipo_comprobante == 'GR':
            tipo_documento = 'una GUIA DE REMISION'

        html = render_to_string(template)
        html = html.replace('${titulo}','Estimado %s<hr>%s le ha emitido %s' % (documento.razon_social_receptor,
                                                                              empresa.nombre_comercial, tipo_documento))
        mensaje = ['<p style="text-align:justify">Podr&aacute; descargarla de los archivos adjuntos o ingresar a la siguiente direcci&oacute;n ']
        mensaje.append('para revisar su comprobante electr&oacute;nico.<br><br>')
        mensaje.append('Recuerde que su usuario es %s@innobeefactura.com ' % documento.identificacion_receptor)
        mensaje.append('y la clave su misma identificaci&oacute;n en caso de ser su primer ingreso a Innobee.</p>')
        html = html.replace('${mensaje}', ''.join(mensaje))
        html = html.replace('${webDomain}', 'https://innobeefactura.com')

        print 'enviar_email_rechazo_comprobante - Enviando a %s...' % emails
        email = EmailMultiAlternatives('Ha recibido %s de %s' % (tipo_documento, empresa.nombre_comercial),
                             ''.join(mensaje), 'info@innobeefactura.com', emails.split(',') )
        email.attach_alternative(html, "text/html")
        email.attach_file(auth_path+'.xml')
        email.attach_file(auth_path+'.pdf')
        email.send()
        print 'enviar_email_rechazo_comprobante - Enviado exitosamente a %s' % email
        return True
    except Exception as e:
        print("Error al enviar el e-mail: {0}".format(e) )
        add_log_error('innobee-util.sndemail', "{0}".format(e))
    return False

import mailchimp


def get_mailchimp_api():
    return mailchimp.Mailchimp('8f6715644ef149bf2a183c466e41a752-us8') #your api key here

def add_log_error(metodo, mensaje):
    try:
        log = core_models.PorLog()
        log.metodo = metodo
        log.componente = 'PORTAL'
        log.tipo = 'ERR'
        log.objeto = mensaje[:255]
        log.fecha_registro = timezone.now()
        log.save()
    except Exception as e:
        print e
        
def bandeja_impresion(request):
    print 'bandeja_impresion - A Imprimir!!'
    return render_to_response('bandeja_impresion.html',{}, context_instance=RequestContext(request))

hoy = datetime.datetime.now()
hoy = hoy.strftime('%Y-%m-%d')

def banners_page(request):
    #print 'banners_page - A desplegar!!'
    banners = core_models.Banner.objects
    banners = banners.extra(where=["%s >= fecha_publicacion"],params=[hoy])
    banners = banners.filter(Q(impresiones_restantes__isnull=True) |
        Q(impresiones_restantes__gt=0)).filter(estado=core_mixins.get_active_status()).order_by('?')
    print 'banners_page - Query', banners.count(), banners.query
    return render_to_response('banners_page.html',{'banners':banners}, context_instance=RequestContext(request))
