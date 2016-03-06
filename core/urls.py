from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^cupones-descuento/$', 'core.views.cupones_descuento'),
    url(r'^campania-publicidad/$', 'core.views.campania_publicidad'),
    url(r'^firma-electronica/$', 'core.views.firma_electronica'),
    url(r'^productos-interes/$', 'core.views.productos_interes'),
)
