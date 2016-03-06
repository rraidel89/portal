from django.conf.urls import patterns, url
from django.contrib.auth.decorators import permission_required
from emisor_receptor.views import EmpresaOperadores, CuponCreateView, \
    CuponEditView, ProductoCreateView, ProductoUpdateView, BannerCreateView, \
    DocumentoEditView, DocumentoCreateView, BannerEditView
from innobee_util.util import CuponPDF, ProductoPDF, bandeja_impresion, banners_page

urlpatterns = patterns('',
                       url(r'^$', 'emisor_receptor.views.inicio'),
                       url(r'^comprobantes-emitidos/$',
                           'emisor_receptor.views.comprobantes_emitidos'),
                       url(r'^comprobantes-recibidos/$',
                           'emisor_receptor.views.comprobantes_recibidos'),
                       url(r'^faqs/$', 'emisor_receptor.views.faqs'),
                       url(r'^reportes/$', 'emisor_receptor.views.reportes'),
                       url(r'^soporte/$', 'emisor_receptor.views.soporte'),
                       url(r'^ayuda/$', 'emisor_receptor.views.ayuda'),
                       url(r'^editar-perfil/$',
                           'emisor_receptor.views.empresa'),
                       url(r'^perfil-persona/$',
                           'emisor_receptor.views.perfil_persona'),
                       url(r'^editar-persona/(?P<cedula>\d+)/$',
                           'emisor_receptor.views.editar_perfil_persona_emisor'),
                       url(r'^update-profile/$', 'emisor_receptor.views.actualizar_perfil_operador'),
                       url(r'^blog/$', 'emisor_receptor.views.blog'),

                       url(r'^comprobantes-cargados/$',
                           'emisor_receptor.views.comprobantes_cargados'),
                       
                       url(r'^cupones-descuento/detalle-cupon/(?P<id_cupon>[a-zA-Z0-9_.-]+)/$', 'emisor_receptor.views.cupon_detalle', name='detalle_cupon'),
                       
                       url(r'^cupones-descuento/cupon-detalle/(?P<id_cupon>\d+)/$', 'emisor_receptor.views.cupon_detalle', name='cupon'),

                       url(r'^productos-interes/producto-detalle/(?P<id_prod>[a-zA-Z0-9_.-]+)/$', 'emisor_receptor.views.producto_detalle', name='producto'),
)

# campanias de publicidad
urlpatterns += patterns('',
    (r'^cupones-descuento/crear-nuevo-cupon/$', permission_required('core.add_cupon')
        (CuponCreateView.as_view())),

    url(r'^cupones-descuento/editar-cupon/(?P<id>\d+)/$',
        permission_required('core.add_cupon')(CuponEditView.as_view())),

    url(r'^campania-publicidad/editar-banner/(?P<id>\d+)/$',
        permission_required('core.add_banner')(BannerEditView.as_view())),

    url(r'^campania-publicidad/editar-campania-email/(?P<id>\d+)/$',
        'emisor_receptor.views.editar_campania_email'),

    url(r'^campania-publicidad/editar-campania-sms/(?P<id>\d+)/$',
        'emisor_receptor.views.editar_campania_sms'),

    url(r'^productos-interes/crear-nuevo-producto/$',
        permission_required('core.add_producto')(ProductoCreateView.as_view())),

    url(r'^productos-interes/editar-producto/(?P<id>\d+)/$',
        permission_required('core.add_producto')(ProductoUpdateView.as_view())),

    url(r'^campania-publicidad/crear-nuevo-banner/$',
        permission_required('core.add_banner')(BannerCreateView.as_view())),

    url(r'^campania-publicidad/crear-nueva-campana/$',
        'emisor_receptor.views.crear_campania_email'),

    url(r'^campania-publicidad/crear-nuevo-sms/$',
        'emisor_receptor.views.crear_campania_sms'),

)

#llamadas a ajax generales
urlpatterns += (
    url(r'^increment_banner_count/$',
        'emisor_receptor.views.increment_banner_count'),

    url(r'^productos-interes/producto-detalle/[0-9]+/increment_print_count_prod/$',
        'emisor_receptor.views.increment_print_count_prod'),

    url(r'^cupones-descuento/cupon-detalle/[0-9]+/increment_print_count_cupon/$',
        'emisor_receptor.views.increment_print_count_cupon'),
)

#exportar datos a xls
urlpatterns += (
    url(r'^export_comp_emit$', 'emisor_receptor.views.export_xls_comp_emit',
        name='exportar_xls'),
    url(r'^export_comp_rec$', 'emisor_receptor.views.export_xls_comp_rec',
        name='exportar_xls'),
    url(r'^export_camp_public$', 'emisor_receptor.views.export_xls_camp_public',
        name='exportar_xls'),
    url(r'^comprobantes-emitidos/export_xls_comp_emit$',
        'emisor_receptor.views.export_xls_comp_emit',
        name='exportar_xls'),

    url(r'^comprobantes-recibidos/export_xls_comp_rec$',
        'emisor_receptor.views.export_xls_comp_emit',
        name='exportar_xls'),
    url(r'^perfil/export_xls_perfiles$',
        'emisor_receptor.views.export_xls_perfiles',
        name='exportar_xls'),

    url(r'^comprobantes-recibidos/export_xls_comp_emit$',
        'emisor_receptor.views.export_xls_comp_rec',
        name='exportar_xls'),

)

urlpatterns += patterns('',
    (r'^cupones-descuento/cupon-detalle/(?P<id_cupon>\d+)/pdf/$', CuponPDF.as_view()),
    
    (r'^bandeja-impresion/$',bandeja_impresion),
    
    (r'^banners-page/$',banners_page),

    (r'^productos-interes/producto-detalle/(?P<id_prod>\d+)/pdf/$',
     ProductoPDF.as_view()),

    (r'^perfil/$', permission_required('core.editar_perfil_empresa')
        (EmpresaOperadores.as_view())),

    url(r'^comprobantes-cargados/editar-comprobante/(?P<id>\d+)/$', (DocumentoEditView.as_view())),
    url(r'^cargar-comprobantes/$', (DocumentoCreateView.as_view())),
)

urlpatterns += patterns('',
    (r'^docs/pdf/(?P<codigo_original>[a-zA-Z0-9_.-]+)/$', 'emisor_receptor.views.view_docs_pdf'),
    (r'^docs/xml/(?P<codigo_original>[a-zA-Z0-9_.-]+)/$', 'emisor_receptor.views.view_docs_xml'),
    (r'^docs/html/(?P<codigo_original>[a-zA-Z0-9_.-]+)/$', 'emisor_receptor.views.view_docs_html'),
    (r'^direct/pdf/(?P<trama>.*)/$', 'emisor_receptor.views.get_direct_pdf'),
)

urlpatterns += patterns('',
    url(r'^reportes-estado/$', 'emisor_receptor.views.reportes_estado'),
    url(r'^export_report_est$', 'emisor_receptor.views.exportar_reporte_estado', name='exportar_reporte_estado_xls'),
    url(r'^reportes-innobee/$', 'emisor_receptor.views.reportes_innobee'),
    url(r'^export_report_inb$', 'emisor_receptor.views.exportar_reporte_innobee', name='exportar_reporte_innobee_xls'),
    url(r'^desactivar_duplicados$', 'emisor_receptor.views.desactivar_duplicados', name='desactivar_duplicados'),
)
