from django.conf.urls import patterns, include, url
#from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from dajaxice.core import dajaxice_autodiscover, dajaxice_config
dajaxice_autodiscover()

from django.conf import settings
from django.conf.urls.static import static
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    (r'^selectable/', include('selectable.urls')), # Selectable fields
    (r'^ckeditor/', include('ckeditor.urls')), # CKEditor
    url(r'^', include('adm.urls')),
    url(r'^', include('emisor_receptor.urls')),
    url(r'^', include('core.urls')),
    url(r'^imprenta-digital/', include('imprenta_digital.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)