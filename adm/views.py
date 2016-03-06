# -*- encoding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import cache_page

from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from django.template.response import TemplateResponse
from helpers import PorOperadorPorCrearHelper
#from forms import PasswordChangeForm
from core import forms as core_forms

from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator

from django.contrib.auth.models import User
import traceback

@cache_page(10)
@ensure_csrf_cookie
def login_user(request):
    '''
    Autentificación de usuarios emisor_receptor
    @param request:
    '''
    template = "login.html"
    context = {}
    ruc1 = username1 = password1 = ''
    if request.method == 'POST':
        username1 = request.POST['username']
        password1 = request.POST['password']
        es_emisor = request.POST['es_emisor']
        try:
            #Busca Ruc en tabla por_operador
            if es_emisor == "True":
                ruc1 = request.POST['ruc']
                user = auth.authenticate(username=username1,
                                        password=password1)
                if user is not None:
                    if user.is_active:
                        profile = user.get_profile()
                        if profile.ruc_empresa:
                            if profile.ruc_empresa.ruc == ruc1:
                                auth.login(request, user)
                                return HttpResponseRedirect("/")
                            else:
                                messages.error(request, 'RUC incorrecto')
                                return render_to_response(template, context,
                                        context_instance=RequestContext(
                                                        request))
                        else:
                            messages.error(request, 'Usuario o contraseña '
                                                    'incorrecto')
                            return render_to_response(template, context,
                                        context_instance=RequestContext(
                                                        request))
                    else:
                        messages.error(request, 'usuario no activo')
                        return render_to_response(template, context,
                                    context_instance=RequestContext(
                                                    request))
                else:
                    messages.error(request, 'Usuario o contraseña incorrecto')
                    return render_to_response(template, context,
                                    context_instance=RequestContext(
                                                        request))
                # else:
                #     messages.error(request, 'Usuario, ruc o contraseña incorrecto')
                #     return render_to_response(template, context,
                #                         context_instance=RequestContext(
                #                                             request))
            else: # Es RECEPTOR
                helper = PorOperadorPorCrearHelper(username1, password1)
                resp = helper.create_if_not_exist()
                
                print 'username1', username1, 'password1', password1
                user = auth.authenticate(username=username1,
                                         password=password1)



                if user is not None:
                    print 'Autenticado', user.username, user.is_active
                    if user.is_active:
                        auth.login(request, user)
                        print ("receptor")
                        if not resp:
                            return HttpResponseRedirect("/")
                        else:
                            return HttpResponseRedirect("/password/change/")
                    else:
                        messages.error(request, 'usuario no activo')
                        return render_to_response(template, context,
                                    context_instance=RequestContext(request))
                else:
                    print 'NO Autenticado'
                    messages.error(request, 'nombre usuario o contraseña incorrecto')
                    return render_to_response(template, context,
                                    context_instance=RequestContext(request))
        except ObjectDoesNotExist:
            messages.error(request, 'usuario, ruc o contraseña incorrecto')
            return render_to_response(template, context,
                                    context_instance=RequestContext(request))
        except Exception as e:
            print 'login - Error inesperado', e
            return render_to_response(template, context,
                              context_instance=RequestContext(request))
    else:
        return render_to_response(template, context,
                              context_instance=RequestContext(request))

def logout_user(request):
    '''
    Cierra la sessión del usuario actual y retorna a la pantalla del login
    @param request:
    '''
    logout(request)
    return HttpResponseRedirect("/")


@login_required
def inicio(request):
    "Función que muestra la página inicial del sistema"
    template = "emisores/index.html"
    """AQUI CARGAR DATOS"""
    return render_to_response(template, {},
                              context_instance=RequestContext(request))


def index(request):
    return render_to_response('emisores/index2.html', {},
                              context_instance=RequestContext(request))

@sensitive_post_parameters()
@csrf_exempt
@login_required
def password_change(request,
                    template_name='password_change.html',
                    post_change_redirect=None,
                    password_change_form=PasswordChangeForm,
                    current_app=None, extra_context=None):
    print 'Password Reset Change - Start'
    if post_change_redirect is None:
        #post_change_redirect = reverse('django.contrib.auth.views.password_change_form')
        post_change_redirect = "/"
    if request.method == "POST":
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            print 'Password Reset Change - Done'
            messages.success(request, 'Su nueva clave fue establecida con exito')
            #return HttpResponseRedirect(post_change_redirect)
            #return TemplateResponse(request, post_change_redirect, {})
            return HttpResponseRedirect(post_change_redirect)
    else:
        form = password_change_form(user=request.user)
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)
       
    print 'Password Reset Change - End'
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)

@csrf_exempt
def password_reset(request, is_admin_site=False,
                   template_name='registration/password_reset_form.html',
                   email_template_name='registration/password_reset_email.html',
                   subject_template_name='registration/password_reset_subject.txt',
                   password_reset_form=PasswordResetForm,
                   token_generator=default_token_generator,
                   post_reset_redirect=None,
                   from_email=None,
                   current_app=None,
                   extra_context=None):
        
    if post_reset_redirect is None:
        post_reset_redirect = "registration/password_reset_done.html"
        
    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': True,
                'token_generator': token_generator,
                'from_email': from_email,
                'email_template_name': email_template_name,
                'subject_template_name': subject_template_name,
                'request': request,
            }
            if is_admin_site:
                opts = dict(opts, domain_override=request.META['HTTP_HOST'])
            form.save(**opts)
            return TemplateResponse(request, post_reset_redirect, {})
    else:
        form = password_reset_form()
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)

    return TemplateResponse(request, template_name, context,
                            current_app=current_app)

@sensitive_post_parameters()
@csrf_exempt
def password_reset_confirm(request, uidb36=None, token=None,
                           template_name='registration/password_reset_confirm.html',
                           token_generator=default_token_generator,
                           set_password_form=SetPasswordForm,
                           post_reset_redirect=None,
                           current_app=None, extra_context=None):
    assert uidb36 is not None and token is not None
    if post_reset_redirect is None:
        post_reset_redirect = "registration/password_reset_complete.html"
    try:
        uid_int = base36_to_int(uidb36)
        user = User.objects.get(id=uid_int)
    except (ValueError, User.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()

                return TemplateResponse(request, post_reset_redirect, {})
        else:
            form = set_password_form(None)
    else:
        validlink = False
        form = None

    context = {
        'form': form,
        'validlink': validlink,
    }
    if extra_context is not None:
        context.update(extra_context)
    
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)

def crear_buzon(request):
    template = 'crear_buzon.html'
    
    form = core_forms.BuzBuzonForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            resp = form.save()
            if resp == 'OK':
                messages.success(request, 'Su buzon ha sido creado con exito, recibira una notificacion con instrucciones en su correo electronico.')
                return HttpResponseRedirect('/')
            else:
                messages.error(request, resp)
        else:
            messages.error(request, 'Existen errores en el formulario')
        
    context = {'form':form}
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def registro_preguntas_secretas_buzon(request):
    template = 'registration/registro_preguntas_secretas.html'
    
    form = core_forms.SecurityQuestionRegistrationForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            resp = form.save(request.user)
            if resp == 'OK':
                messages.success(request, 'Las preguntas secretas han sido actualizadas en su buzon por su seguridad.')
                return HttpResponseRedirect('/')
            else:
                messages.error(request, resp)
        else:
            messages.error(request, 'Existen errores en el formulario')
        
    context = {'form':form}
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def acceso_usuario_reseteo(request):
    template = 'registration/acceso_usuario_reseteo.html'
    
    form = core_forms.UserAccessForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            resp, usuario = form.save()
            if resp == 'OK':
                return HttpResponseRedirect('/preguntas-acceso/%d/' % usuario.id)
            else:
                messages.error(request, resp)
        else:
            messages.error(request, 'Existen errores en el formulario')
        
    context = {'form':form}
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def preguntas_secretas_buzon(request, usuario_id):
    template = 'registration/preguntas_secretas.html'
    
    try:
        usuario = User.objects.get(pk = usuario_id)
    except Exception as e:
        messages.error(request, 'El usuario no existe: %s' % str(e))
        return HttpResponseRedirect('/')
    
    form = core_forms.SecurityAnswersForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            resp = form.save(usuario)
            if resp == 'OK':
                uidb36 = int_to_base36(usuario.id)
                token = default_token_generator.make_token(usuario)
                return HttpResponseRedirect('/password/reset/confirm/%s-%s/' % (str(uidb36),str(token)))
            else:
                messages.error(request, resp)
        else:
            messages.error(request, 'Existen errores en el formulario')
    
    try:
        perfil = usuario.get_profile()
        if perfil.pregunta_1 is None or perfil.pregunta_2 is None:
            messages.error(request, 'El usuario no ha establecido sus preguntas de seguridad.')
            return HttpResponseRedirect('/')
    except:
        messages.error(request, 'El usuario no esta activo')
        return HttpResponseRedirect('/')
    
    context = {'form':form, 'profile':perfil}
    
    return render_to_response(template, context, context_instance=RequestContext(request))

def base36_to_int(s):
    return int(s, 36)

def int_to_base36(i):
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    factor = 0
    # Find starting factor
    while True:
        factor += 1
        if i < 36 ** factor:
            factor -= 1
            break
    base36 = []
    # Construct base36 representation
    while factor >= 0:
        j = 36 ** factor
        base36.append(digits[i / j])
        i = i % j
        factor -= 1
    return ''.join(base36)

