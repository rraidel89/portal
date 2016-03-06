from selectable.base import ModelLookup
from selectable.registry import registry
import selectable.forms as selectable

from core import models as core_models
from core import mixins as core_mixins
from imprenta_digital import models as impd_models
from innobee_portal import messages as __

from django.contrib.admin.widgets import AdminTextInputWidget
from django.utils.safestring import mark_safe
# Smart encoding unicode
from django.utils.encoding import smart_unicode

estado_activo = core_mixins.get_active_status()

class ProductSearchWidget(selectable.AutoCompleteSelectWidget):
    def render(self, name=None, value=None, attrs=None):
        widget = super(ProductSearchWidget, self).render(name, value, attrs)
        function_call = 'new_product(this)'
        remove_function_call = 'clear_product(this)'
        html = [u'%s&nbsp;&nbsp;' % widget]
        html.append(u'<a href="javascript:void(0)" onclick="%s" class="btn btn-info btn-sm"><i class="fa fa-external-link"></i>&nbsp;</a>' % function_call)
        html.append(u'<a href="javascript:void(0)" onclick="%s" class="btn btn-danger btn-sm"><i class="fa fa-eraser"></i>&nbsp;</a>' % remove_function_call)
        return mark_safe(''.join(html))

def get_producto_factura_lookup_widget(ruc_empresa):
    """ Construye un widget lookup para autobus """
    print 'get_productos_lookup_widget - Para empresa', ruc_empresa
    class ProductoFacturaLookup(ModelLookup):
        model = impd_models.ImpdProducto
        search_fields = ('descripcion__icontains', 'codigo_principal__icontains', 'codigo_secundario__icontains')
        filters = {'estado': estado_activo, 'ruc_empresa':ruc_empresa}
    
        def get_item_label(self, item):
            return u'%s, %s' % (item.codigo_principal, item.descripcion)
    
    try:
        registry.unregister(ProductoFacturaLookup)
    except:
        pass
    
    try:
        registry.register(ProductoFacturaLookup)
    except:
        pass
    
    return ProductSearchWidget(lookup_class=ProductoFacturaLookup,
                                               attrs={'placeholder': __.PH_PRODUCTO, 'class':'big-field', 'size':'30'})
    
class ClientSearchWidget(selectable.AutoCompleteSelectWidget):
    def render(self, name=None, value=None, attrs=None):
        widget = super(ClientSearchWidget, self).render(name, value, attrs)
        return mark_safe(u'%s&nbsp;&nbsp;<a href="#modal-crear-cliente" '
                         u'data-toggle="modal" class="btn btn-primary" onclick="completeClearForm(\'form_crear_cliente\')"><i class="fa fa-plus"></i>&nbsp;</a>' % widget)

def get_cliente_lookup_widget(ruc_empresa):
    """ Construye un widget lookup para autobus """
    print 'get_cliente_lookup_widget - Para empresa', ruc_empresa
    class ClienteLookup(ModelLookup):
        model = impd_models.ImpdCliente
        search_fields = ('identificacion__icontains', 'razon_social__icontains')
        filters = {'estado': estado_activo, 'ruc_empresa':ruc_empresa}
    
        def get_item_label(self, item):
            return u'%s, %s' % (item.identificacion, item.razon_social)
    
    try:
        registry.register(ClienteLookup)
    except:
        pass
    
    return ClientSearchWidget(lookup_class=ClienteLookup, attrs={'placeholder': __.PH_CLIENTE, 'class':'search_input', 'size':'30'})

class ConfigSearchWidget(selectable.AutoCompleteSelectWidget):
    def render(self, name=None, value=None, attrs=None):
        widget = super(ConfigSearchWidget, self).render(name, value, attrs)
        func = 'completeClearForm("form_crear_config")'
        return mark_safe(u'%s&nbsp;&nbsp;<a href="#modal-crear-configuracion" '
                         u'data-toggle="modal" onclick="%s" class="btn btn-primary"><i class="fa fa-plus"></i>&nbsp;</a>' % (widget, func))
        
        
def get_factura_config_lookup_widget(ruc_empresa):
    """ Construye un widget lookup para autobus """
    print 'get_factura_config_lookup_widget - Para empresa', ruc_empresa
    class FacturaConfigLookup(ModelLookup):
        model = impd_models.ImpdFacturaConfiguracion
        search_fields = ('descripcion__icontains', 'establecimiento__icontains')
        filters = {'estado': estado_activo, 'ruc_empresa':ruc_empresa}
    
        def get_item_label(self, item):
            return u'%s, %s' % (item.establecimiento, item.descripcion)
    
    try:
        registry.register(FacturaConfigLookup)
    except:
        pass
    
    return ConfigSearchWidget(lookup_class=FacturaConfigLookup, attrs={'placeholder': __.PH_CONFIG, 'class':'search_input', 'size':'30'})

class DestinatarioSearchWidget(selectable.AutoCompleteSelectWidget):
    def render(self, name=None, value=None, attrs=None):
        widget = super(DestinatarioSearchWidget, self).render(name, value, attrs)
        function_call = 'new_destinatario(this)'
        remove_function_call = 'clear_destinatario(this)'
        html = [u'%s&nbsp;&nbsp;' % widget]
        html.append(u'<a href="javascript:void(0)" onclick="%s" class="btn btn-info btn-sm"><i class="fa fa-external-link"></i>&nbsp;</a>' % function_call)
        html.append(u'<a href="javascript:void(0)" onclick="%s" class="btn btn-danger btn-sm"><i class="fa fa-eraser"></i>&nbsp;</a>' % remove_function_call)
        return mark_safe(''.join(html))
    
def get_destinatario_lookup_widget(ruc_empresa):
    """ Construye un widget lookup para autobus """
    print 'get_destinatario_lookup_widget - Para empresa', ruc_empresa
    class DestinarioLookup(ModelLookup):
        model = impd_models.ImpdGRDestinatario
        search_fields = ('identificacion_destinatario__icontains', 'razon_social_destinatario__icontains')
        filters = {'estado': estado_activo, 'ruc_empresa':ruc_empresa}
    
        def get_item_label(self, item):
            return u'%s' % item.get_descripcion()
    
    try:
        registry.unregister(DestinarioLookup)
    except:
        pass    
    registry.register(DestinarioLookup)
    
    return DestinatarioSearchWidget(lookup_class=DestinarioLookup,
                                               attrs={'placeholder': __.PH_DESTINATARIO, 'class':'big-field', 'size':'30'})
