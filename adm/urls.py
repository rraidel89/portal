# -*- encoding: utf-8 -*-
from django.conf.urls import patterns, url

from django.contrib.auth import views as auth_views

urlpatterns = patterns('',
    url(r'^accounts/login/$', 'adm.views.login_user'),
    url(r'^logout/$', 'adm.views.logout_user'),
    #url(r'^$', 'adm.views.inicio'),
    url(r'^index/$', 'adm.views.index'),
    url(r'^crear-buzon/$', 'adm.views.crear_buzon', name='crear-buzon'),
    url(r'^acceso-reseteo/$', 'adm.views.acceso_usuario_reseteo', name='acceso-reseteo'),
    url(r'^registro-preguntas/$', 'adm.views.registro_preguntas_secretas_buzon', name='registro-preguntas'),
    url(r'^preguntas-acceso/(?P<usuario_id>[0-9]+)/$', 'adm.views.preguntas_secretas_buzon', name='preguntas-acceso'),
    
    url(r'^password/change/$', 'adm.views.password_change', name='auth_password_change'),
    url(r'^password/reset/$', 'adm.views.password_reset' , name='auth_password_reset'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'adm.views.password_reset_confirm', name='auth_password_reset_confirm'),
    url(r'^password/reset/complete/$', auth_views.password_reset_complete, name='auth_password_reset_complete'),
    url(r'^password/reset/done/$', auth_views.password_reset_done, name='auth_password_reset_done'),
)
