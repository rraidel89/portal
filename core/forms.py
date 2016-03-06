from django.db import IntegrityError, transaction
from django import forms
from django.forms.widgets import Textarea, TextInput
from django.utils.encoding import smart_unicode
from django.contrib.auth.models import User
from django.conf import settings

from innobee_portal import properties as P
from core.validators import doc_validator
import models
import traceback

try:
    import SOAPpyOld
except:
    #traceback.print_exc()
    import SOAPpy as SOAPpyOld

class BuzBuzonForm(forms.Form):
    tipo_identificacion = forms.ChoiceField(choices=[(k, v) for k, v in P.TIPOS_IDENTIFICACION_COMPLETA_CHOICES],
                                            label='Tipo de Identificacion', required=True)    
    identificacion = forms.CharField(label='Identificacion', widget=TextInput(attrs={'size': '13'}), required=True)
    razon_social = forms.CharField(label='Razon Social', widget=TextInput(attrs={'size': '100'}), required=True)
    nombres = forms.CharField(label='Nombres', widget=TextInput(attrs={'size': '32'}), required=True)
    apellidos = forms.CharField(label='Apellidos', widget=TextInput(attrs={'size': '32'}), required=True)
    email_notificacion = forms.EmailField(label='Email Principal', required=True)
    tipo_persona = forms.ModelChoiceField(queryset=models.PorTipoPersona.objects.all(),
                                            label='Tipo de Persona', required=True)
    
    def get_tipo_cliente(self):
        tipos = models.PorTipoCliente.objects.filter(nombre = 'BUZON')
        if tipos.count() == 0:
            tipo = models.PorTipoCliente()
            tipo.nombre = 'BUZON'
            tipo.save()
        else:
            tipo = tipos[0]
        return tipo
    
    def save(self, commit=False):
        try:
            savepoint = transaction.savepoint()
            cleaned_data = self.cleaned_data.copy()
            
            tipo_identificacion = cleaned_data.pop('tipo_identificacion', None)
            identificacion = cleaned_data.pop('identificacion', None)
            razon_social = cleaned_data.pop('razon_social', None)
            nombres = cleaned_data.pop('nombres', None)
            apellidos = cleaned_data.pop('apellidos', None)
            email_notificacion = cleaned_data.pop('email_notificacion', None)
            tipo_persona = cleaned_data.pop('tipo_persona', None)
            if not isinstance(tipo_persona, models.PorTipoPersona):
                try:
                    tipo_persona = models.PorTipoPersona.objects.get(pk=tipo_persona)
                except:
                    pass
            
            tipo_persona = tipo_persona.nombre.upper()            
            tipo_cliente = self.get_tipo_cliente().nombre
            email_buzon = identificacion 
            password_usuario = identificacion
            
            namespace = settings.BUZON_WS_NAMESPACE
            proxy = SOAPpyOld.SOAPProxy(settings.BUZON_WS_URL, namespace = namespace, soapaction = settings.BUZON_WS_CREATE_ACTION)
            proxy.config.debug = 1
            
            if doc_validator.find_special_ruc(identificacion):
                print 'Conectandose con servicio Metodo 2...'
                resp = proxy.crearBuzonSimpleNoValidar(SOAPpyOld.Types.untypedType(name = (namespace, "arg5"), data = tipo_cliente),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg4"), data = identificacion),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg3"), data = tipo_identificacion),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg2"), data = settings.BUZON_WS_SEC_PWD),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg1"), data = settings.BUZON_WS_SEC_USER),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg0"), data = settings.BUZON_WS_SEC_RUC),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg10"), data = email_notificacion),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg6"), data = tipo_persona),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg7"), data = razon_social),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg8"), data = nombres),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg9"), data = apellidos))                                         
            else:
                print 'Conectandose con servicio Metodo 1...'
                resp = proxy.crearBuzonSimple(SOAPpyOld.Types.untypedType(name = (namespace, "arg5"), data = tipo_cliente),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg4"), data = identificacion),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg3"), data = tipo_identificacion),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg2"), data = settings.BUZON_WS_SEC_PWD),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg1"), data = settings.BUZON_WS_SEC_USER),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg0"), data = settings.BUZON_WS_SEC_RUC),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg10"), data = email_notificacion),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg6"), data = tipo_persona),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg7"), data = razon_social),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg8"), data = nombres),
                                              SOAPpyOld.Types.untypedType(name = (namespace, "arg9"), data = apellidos))
            
            try:
                codigoError = resp['codigoError']
                transaction.savepoint_commit(savepoint)
                if codigoError == '0':
                    return 'OK'
                
                message = resp['mensajeError']
                if message.find('ACCOUNT_EXISTS') >= 0:
                    message = 'La cuenta de buzon con identificacion %s ya fue registrada anteriormente' % identificacion
                '''
                elif message.find('RUC no supera las pruebas de validez iniciales') >= 0:
                    if doc_validator.find_special_ruc(identificacion):
                        return 'OK'    
                '''
                return message
            except Exception as e1:
                print 'BuzBuzonForm - Error recepcion respuesta', e1
        except Exception as e:            
            transaction.savepoint_rollback(savepoint)
            traceback.print_exc()
        return 'Error inesperado al procesar su solicitud'

class SecurityQuestionRegistrationForm(forms.Form):
    
    pregunta_1 = forms.ChoiceField(choices=[(k, v) for k, v in P.PREGUNTAS_PREDEFINIDAS_CHOICES],
                                            label='Pregunta #1 (Predefinida)', required=True)
    
    respuesta_1 = forms.CharField(label='Respuesta #1', widget=TextInput(attrs={'size': '50'}),
                                 required=True)
    
    pregunta_2 = forms.CharField(label='Pregunta #2 (Realice su propia pregunta)', widget=TextInput(attrs={'size': '50'}),
                                 required=True)    
    
    respuesta_2 = forms.CharField(label='Respuesta #2 (La respuesta a su pregunta)', widget=TextInput(attrs={'size': '50'}),
                                 required=True)
    
    def save(self, user):
        try:
            cleaned_data = self.cleaned_data.copy()
            operador = user.get_profile()
            operador.pregunta_1 = cleaned_data.pop('pregunta_1', None)
            operador.respuesta_1 = cleaned_data.pop('respuesta_1', None)
            operador.pregunta_2 = cleaned_data.pop('pregunta_2', None)
            operador.respuesta_2 = cleaned_data.pop('respuesta_2', None)
            operador.save()
            return 'OK'
        except Exception as e:
            print 'Error al actualizar buzon', e
        
        return 'Error inesperado al actualizar datos del buzon'

class UserAccessForm(forms.Form):
    
    nombre_usuario = forms.CharField(label='Nombre de Usuario', widget=TextInput(attrs={'size': '50'}),
                                 required=True)
    
    def save(self):
        try:
            cleaned_data = self.cleaned_data.copy()
            usuario = User.objects.get(username = cleaned_data.pop('nombre_usuario', None))
            return 'OK', usuario
        except Exception as e:
            return 'Lo sentimos. El usuario no existe: %s' % str(e), None
    
class SecurityAnswersForm(forms.Form):
    
    respuesta_1 = forms.CharField(label='Respuesta #1', widget=TextInput(attrs={'size': '50'}),
                                 required=True)
    
    respuesta_2 = forms.CharField(label='Respuesta #2', widget=TextInput(attrs={'size': '50'}),
                                 required=True)
    
    def save(self, usuario):        
        try:
            cleaned_data = self.cleaned_data.copy()
            operador = usuario.get_profile()
            
            respuesta_1 = cleaned_data.pop('respuesta_1', None)
            respuesta_1 = respuesta_1.strip().lower()
            
            respuesta_2 = cleaned_data.pop('respuesta_2', None)
            respuesta_2 = respuesta_2.strip().lower()
            
            resp1 = operador.respuesta_1.strip().lower()
            resp2 = operador.respuesta_2.strip().lower()
            
            if resp1 == respuesta_1 and resp2 == respuesta_2:
                return 'OK'
            return 'Las respuestas no coinciden'
        except Exception as e:
            print 'Error al actualizar buzon', e 
        return 'Error inesperado al verificar las respuestas secretas'
