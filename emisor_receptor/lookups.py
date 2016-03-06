from selectable.base import ModelLookup
from selectable.registry import registry
import selectable.forms as selectable

from core import models as core_models
from core import mixins as core_mixins
from imprenta_digital import models as impd_models
from innobee_portal import messages as __

# Smart encoding unicode
from django.utils.encoding import smart_unicode

estado_activo = core_mixins.get_active_status()

def get_productos_lookup_widget(ruc_empresa):
    """ Construye un widget lookup para autobus """
    print 'get_productos_lookup_widget - Para empresa', ruc_empresa
    class ProductoLookup(ModelLookup):
        model = core_models.Producto
        search_fields = ('nombre__icontains', 'titulo__icontains', 'codigo_sku__icontains')
        filters = {'estado': estado_activo, 'ruc_empresa':ruc_empresa}

        def get_item_label(self, item):
            return u'%s, %s' % (item.codigo_sku, item.nombre)
    
    try:
        registry.register(ProductoLookup)
    except Exception as e:
        print 'SELECTABLE ERROR', e 
    
    return selectable.AutoCompleteSelectWidget(lookup_class=ProductoLookup, attrs={'placeholder': __.PH_PRODUCTO, 'class':'form-control'})
