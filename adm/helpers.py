from django.contrib.auth.models import User
from django.http import HttpResponseRedirect

from core.models import PorOperadorPorCrear, PorOperador, BuzBuzon, PorEmpresa
from core.validators import doc_validator
from innobee_portal import properties as P
from imprenta_digital import models as impd_models

import datetime
import traceback

from django.db import IntegrityError, transaction

class PorOperadorPorCrearHelper(object):
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def create_if_not_exist(self):
        try:
            operador_por_crear = PorOperadorPorCrear.objects.get(usuario = self.username, creado=False)
            return self.crear_operador(operador_por_crear)
        except Exception as e:
            print 'create_if_not_exist - Error:', e
            self.create_cliente_if_not_exist(self.username)
        
        return False
    
    def user_exist(self, username):
        if User.objects.filter(username=username).count():
            return True
        return False
    
    def crear_operador(self, operador_por_crear):
        try:
            user = User.objects.get(username = operador_por_crear.usuario)
        except:
            try:
                user = User.objects.create_user(username=operador_por_crear.usuario,
                                        email=operador_por_crear.usuario,
                                        password=operador_por_crear.clave) 
            except:
                return False
        
        try:
            user.first_name = operador_por_crear.nombres[:64]
            user.last_name = operador_por_crear.apellidos[:64]
            user.save()
        except Exception as e:
            print e
        
        try:
            print 'Usuario creado, registrando operador y atando usuario'
            savepoint = transaction.savepoint()
            por_operador = PorOperador()
            por_operador.identificacion = operador_por_crear.identificacion
            por_operador.tipo_identificacion = self.get_tipo_identificacion(por_operador.identificacion)
            por_operador.nombres = operador_por_crear.nombres
            por_operador.apellidos = operador_por_crear.apellidos
            por_operador.email_principal = operador_por_crear.usuario
            por_operador.email_secundario = operador_por_crear.email_secundario
            por_operador.user = user
            por_operador.fecha_actualizacion = datetime.datetime.now()
            por_operador.fecha_creacion = datetime.datetime.now()
            por_operador.usuario_creacion = operador_por_crear.usuario[:31]
            por_operador.save()
                        
            self.create_cliente_if_not_exist(operador_por_crear.usuario)
            
            print 'Operador creado, actualizando operador por crear', operador_por_crear.pk
            try:
                operador_por_crear.creado = True
                operador_por_crear.fecha_actualizacion = datetime.datetime.now()
                operador_por_crear.save()
            except Exception as ex:
                traceback.print_exc()
                print 'Error actualizando Operador Por Crear', ex                
            print  'Todo OK. Haciendo Commit'
            transaction.savepoint_commit(savepoint)
        except Exception as e:
            transaction.savepoint_rollback(savepoint)
            return False
        return True

    def crear_operador_from_buzon(self, buzon):
        try:
            print 'B.1 -> Usuario creado, registrando operador y atando usuario', buzon.identificacion
            savepoint = transaction.savepoint()

            user = User.objects.create_user(username=buzon.email_buzon,
                                email=buzon.email_buzon,
                                password=buzon.identificacion)

            user.first_name = buzon.nombres[:64]
            user.last_name = buzon.apellidos[:64]
            user.save()

            por_operador = PorOperador()
            por_operador.identificacion = buzon.identificacion
            por_operador.tipo_identificacion = self.get_tipo_identificacion(buzon.identificacion)
            por_operador.nombres = buzon.nombres
            por_operador.apellidos = buzon.apellidos
            por_operador.email_principal = buzon.email_buzon
            por_operador.email_secundario = buzon.email_notificacion
            por_operador.user = user
            por_operador.fecha_actualizacion = datetime.datetime.now()
            por_operador.fecha_creacion = datetime.datetime.now()
            por_operador.usuario_creacion = buzon.identificacion
            por_operador.save()

            print 'B.2 -> Operador creado', buzon.identificacion
            transaction.savepoint_commit(savepoint)
        except Exception as e:
            print 'Error', e
            traceback.print_exc()
            transaction.savepoint_rollback(savepoint)
            return False
        return True

    def create_cliente_if_not_exist(self, username):
        try:
            operador_por_crear = PorOperadorPorCrear.objects.get(usuario = self.username, creado=True)
            if operador_por_crear and operador_por_crear.ruc_empresa:
                try:
                    impd_models.ImpdCliente.objects.get(identificacion = operador_por_crear.identificacion)
                except Exception as ex:
                    print 'create_cliente_if_not_exist - No existe IMPD Cliente:', ex
                    self.crear_cliente(operador_por_crear)
        except Exception as e:
            try:
                try:
                    User.objects.get(username = self.username)
                    print '<-- Todos los elementos de', self.username, 'fueron creados.'
                except:
                    buzon_por_crear_operador = BuzBuzon.objects.get(email_buzon = self.username)
                    self.crear_operador_from_buzon(buzon_por_crear_operador)
            except Exception as ex:
                print 'create_cliente_if_not_exist - Error:', e

    
    def get_tipo_identificacion(self, identificacion):
        if len(identificacion) == 13:
            if doc_validator.validar_ruc(identificacion):
                return P.TID_RUC
        elif len(identificacion) == 10:
            if doc_validator.validar_cedula(identificacion):
                return P.TID_CEDULA
        return P.TID_PASAPORTE
    
    def crear_cliente(self, operador_por_crear):
        try:
            print 'Intentando crear cliente ', operador_por_crear.identificacion, 'de empresa:', operador_por_crear.ruc_empresa
            if operador_por_crear.identificacion and operador_por_crear.ruc_empresa:
                print 'crear_cliente - Creando Cliente...'
                cliente = impd_models.ImpdCliente()
                cliente.email_principal = operador_por_crear.usuario
                cliente.email_secundario = operador_por_crear.email_secundario
                cliente.ruc_empresa = PorEmpresa.objects.get(pk=operador_por_crear.ruc_empresa)
                cliente.tipo_identificacion = self.get_tipo_identificacion(operador_por_crear.identificacion)
                cliente.identificacion = operador_por_crear.identificacion
                cliente.razon_social = operador_por_crear.nombres + " " + operador_por_crear.apellidos
                cliente.save()
                print 'crear_cliente - Cliente Creado'
            else:
                print 'crear_cliente - El cliente no tiene datos'
        except Exception as e:
            print 'Error al crerar cliente', e
            

class BuzonRedirectHelper(object):
    
    def __init__(self, user):
        try:
            self.profile = user.get_profile()
        except:
            self.profile = None
    
    def has_profile(self):
        return self.profile is not None
    
    def verificar_buzon_completo(self):
        try:
            if self.profile.pregunta_1 and self.profile.pregunta_2:
                return True
            return False
        except Exception as e:
            print 'No existe buzon', e
            return True
    
    def redirigir(self):
        return HttpResponseRedirect('/registro-preguntas')
    