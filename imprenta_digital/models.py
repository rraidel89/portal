
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponse

from core import mixins

from innobee_portal import properties as P

from helpers import catalogo_helper

from django.db.models import Sum

'''
------------------------------------
Modelos para Imprenta Digital
------------------------------------
'''

class ImpdCliente(mixins.AuditMixin):
    ruc_empresa = models.ForeignKey('core.PorEmpresa', db_column='ruc_empresa')
    tipo_identificacion = models.CharField(max_length=2, choices = catalogo_helper.get_catalogo(P.CAT_TIPO_IDENTIFICACION))
    identificacion = models.CharField(max_length=20, unique=True)
    razon_social = models.CharField(max_length=300)
    email_principal = models.CharField(max_length=64)
    email_secundario = models.CharField(max_length=64, blank=True)
    direccion_comprador = models.CharField(max_length=300, blank=True, null=True)
    
    def __unicode__(self):
        return u'%s | %s' % (self.identificacion, self.razon_social)
    
    class Meta:
        db_table = 'impd_cliente'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

class IMPDFacturaExportadoresMixin(mixins.IMPDComprobanteMixin):
    comercio_exterior = models.CharField(max_length=32, blank=True)
    inco_term_factura = models.CharField(max_length=10, blank=True)
    lugar_inco_term = models.CharField(max_length=300, blank=True)
    pais_origen = models.CharField(max_length=3, choices = catalogo_helper.get_catalogo(P.CAT_EXP_PAISES), blank=True)
    puerto_embarque = models.CharField(max_length=300, blank=True)
    puerto_destino = models.CharField(max_length=300, blank=True)
    pais_destino = models.CharField(max_length=3, choices = catalogo_helper.get_catalogo(P.CAT_EXP_PAISES), blank=True)
    pais_adquisicion = models.CharField(max_length=3, choices = catalogo_helper.get_catalogo(P.CAT_EXP_PAISES), blank=True)
    inco_term_total_sin_impuestos = models.CharField(max_length=10, blank=True)
    flete_internacional = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    seguro_internacional = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gastos_aduaneros = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gastos_transporte_otros = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        abstract = True

class IMPDFacturaReembolsoMixin(IMPDFacturaExportadoresMixin):
    total_comprobantes_reembolso = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    total_base_imponible_reembolso = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    total_impuesto_reembolso = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    valor_ret_iva = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    valor_ret_renta = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    cod_doc_reembolso = models.CharField(max_length=2, blank=True,
                                         choices = catalogo_helper.get_catalogo(P.CAT_TIPO_DOCUMENTO))

    class Meta:
        abstract = True

class ImpdFactura(IMPDFacturaReembolsoMixin):
    ruc_empresa = models.ForeignKey('core.PorEmpresa', db_column='ruc_empresa')
    id_cliente = models.ForeignKey('ImpdCliente', db_column='id_cliente')
    fecha_emision = models.DateField()
    total_sin_impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado_pago = models.CharField(max_length=10, choices=P.ESTADO_PAGO_PAGADO_CHOICES, default=P.ESTADO_PAGO_PAGADO)
    
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    propina = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    guia_remision = models.CharField(max_length=17, blank=True)

    # Campo especiales
    secuencial_number = models.IntegerField(default=0, blank=True)
    
    def str_total_sin_impuestos(self):
        return '%.2f' % self.total_sin_impuestos
    
    def str_descuento(self):
        return '%.2f' % self.descuento
    
    def str_iva(self):
        return '%.2f' % self.iva
    
    def str_total(self):
        return '%.2f' % self.total
    
    def str_propina(self):
        return '%.2f' % self.propina
    
    def get_guia_remision(self):
        return self.guia_remision
    
    def get_fecha_emision(self):
        return self.fecha_emision.strftime("%d/%m/%Y")
    
    def get_impuestos_grouped(self):
        factura = ImpdFactura.objects.get(pk = self.pk)
        items = factura.impditemfactura_set.all()
        impuestos = ImpdItemFacturaImpuesto.objects.filter(item_factura__in = items)\
            .values('producto_impuesto__codigo_impuesto','producto_impuesto__codigo_porcentaje','producto_impuesto__tarifa')\
            .annotate(valor = Sum('valor'), base_imponible = Sum('base_imponible'))
        return impuestos
    
    def get_subtotals_dict(self):
        subtotal12 = 0
        subtotal0 = 0
        subtotal_na = 0
        subtotal_ei = 0
        impuestos = self.get_impuestos_grouped()
        for totalConImp in impuestos:
            if totalConImp['producto_impuesto__codigo_porcentaje'] == '0':
                subtotal0 += float(totalConImp['base_imponible'])
            elif totalConImp['producto_impuesto__codigo_porcentaje'] == '2':
                subtotal12 += float(totalConImp['base_imponible'])
            elif totalConImp['producto_impuesto__codigo_porcentaje'] == '6':
                subtotal_na += float(totalConImp['base_imponible'])
            elif totalConImp['producto_impuesto__codigo_porcentaje'] == '7':
                subtotal_ei += float(totalConImp['base_imponible'])
        
        return {
            'subtotal12':subtotal12,
            'subtotal0':subtotal0,
            'subtotal_na':'%.2f' %subtotal_na,
            'subtotal_ei':'%.2f' %subtotal_ei,
        }
    
    def get_totales(self):
        items = self.impditemfactura_set.all()
        total_sin_impuestos = 0
        total_impuestos = 0
        total_descuentos = 0
        
        for item in items:
            total_descuentos += float(item.descuento)
            subtotal = (float(item.cantidad) * float(item.id_producto.precio_unitario)) - float(item.descuento)
            impuestos_producto = float(item.id_producto.get_impuestos(subtotal))
            total_impuestos += impuestos_producto
            total_sin_impuestos += float(subtotal)
                
        return {
            'total_sin_impuestos':'%.2f' %total_sin_impuestos,
            'total_impuestos':'%.2f' %total_impuestos,
            'total_descuentos':'%.2f' %total_descuentos,
            'total':'%.2f' %(total_sin_impuestos + total_impuestos),
        }

    def get_items(self):
        items = self.impditemfactura_set.all()
        items = items.order_by('fecha_actualizacion').reverse()
        return items

    def get_info_adicional(self):
        items = self.impdfacturainformacionadicional_set.all()
        items = items.order_by('fecha_actualizacion').reverse()
        return items
    
    class Meta:
        db_table = 'impd_factura'
        verbose_name = 'Factura Digital'
        verbose_name_plural = 'Facturas Digitales'

class ImpdFacturaInformacionAdicional(mixins.AuditMixin):
    nombre = models.CharField(max_length=50)
    valor = models.CharField(max_length=300)
    factura = models.ForeignKey('ImpdFactura', db_column='id_factura')
    
    def __unicode__(self):
        return u'%s = %s' % (self.nombre, self.valor)
    
    class Meta:
        db_table = 'impd_factura_informacion_adicional'
        verbose_name = 'Informacion Adicional de Factura'
        verbose_name_plural = 'Informaciones Adicionales de Facturas'

class ImpdFacturaConfiguracion(mixins.AuditMixin):
    establecimiento = models.CharField(max_length=3)
    punto_emision = models.CharField(max_length=3)
    moneda = models.CharField(max_length=15, blank=True, choices = catalogo_helper.get_catalogo(P.CAT_IMPRENTA_DIGITAL_MONEDA))
    ruc_empresa = models.ForeignKey('core.PorEmpresa', db_column='ruc_empresa')
    secuencial_inicial = models.CharField(max_length=9, blank=True)
    descripcion = models.CharField(max_length=32, blank=True)
    
    
    def __unicode__(self):
        return u'%s' % self.descripcion
    
    class Meta:
        db_table = 'impd_factura_configuracion'
        verbose_name = 'Configuracion Factura Digital'
        verbose_name_plural = 'Configuracion Facturas Digitales'

class ImpdItemFactura(mixins.AuditMixin):
    id_factura = models.ForeignKey('ImpdFactura', db_column='id_factura')
    id_producto = models.ForeignKey('ImpdProducto', db_column='id_producto')
    cantidad = models.DecimalField(max_digits=14, decimal_places=6, default=1)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_sin_impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    def get_impuestos(self):
        print 'BUSCANDO', self.pk
        impuestos = ImpdItemFacturaImpuesto.objects.filter(item_factura__id = self.pk)
        print 'IMPUESTOS', impuestos
        return impuestos
    
    def str_cantidad(self):
        return '%.2f' % self.cantidad
    
    def str_descuento(self):
        return '%.2f' % self.descuento
    
    def str_total_sin_impuestos(self):
        return '%.2f' % self.total_sin_impuestos
    
    class Meta:
        db_table = 'impd_item_factura'
        verbose_name = 'Item Factura Digital'
        verbose_name_plural = 'Items Factura Digital'

class ImpdItemFacturaImpuesto(mixins.AuditMixin):
    base_imponible = models.DecimalField(max_digits=14, decimal_places=2, default=1)
    valor = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    item_factura = models.ForeignKey('ImpdItemFactura', db_column='id_item_factura')
    producto_impuesto = models.ForeignKey('ImpdProductoImpuesto', db_column='id_producto_impuesto')
    
    def str_base_imponible(self):
        return '%.2f' % self.base_imponible
    
    def str_valor(self):
        return '%.2f' % self.valor
    
    class Meta:
        db_table = 'impd_item_factura_impuesto'
        verbose_name = 'Impuesto Item Factura Digital'
        verbose_name_plural = 'Impuestos Items Factura Digital'

class ImpdProducto(mixins.AuditMixin):
    codigo_principal = models.CharField(max_length=15)
    codigo_secundario = models.CharField(max_length=15)
    descripcion = models.CharField(max_length=200)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=6)
    ruc_empresa = models.ForeignKey('core.PorEmpresa', db_column='ruc_empresa')
    
    def str_precio_unitario(self):
        return '%.3f' % self.precio_unitario
    
    def __unicode__(self):
        return u'%s - %s | %s' % (self.codigo_principal, self.codigo_secundario, self.descripcion[:30])
    
    def get_impuestos(self, subtotal):
        impuestos_item = 0
        for prod_imp in self.impdproductoimpuesto_set.all():
            valor = float(prod_imp.tarifa) * 0.01 * float(subtotal)
            impuestos_item += valor
        return impuestos_item
    
    class Meta:
        db_table = 'impd_producto'
        verbose_name = 'Producto para Factura'
        verbose_name_plural = 'Productos para Facturas'

class ImpdProductoDetalleAdicional(mixins.AuditMixin):
    nombre = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=300)
    id_producto = models.ForeignKey('ImpdProducto', db_column='id_producto')
    
    class Meta:
        db_table = 'impd_producto_detalle_adicional'
        verbose_name = 'Detalle Adicional de Producto'
        verbose_name_plural = 'Detalles Adicionales de Productos'

class ImpdProductoImpuesto(mixins.AuditMixin):
    codigo_impuesto = models.CharField(max_length=1, choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_CODIGO_IMPUESTO))
    codigo_porcentaje = models.CharField(max_length=4, choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_CODIGO_PORCENTAJE))
    tarifa = models.DecimalField(max_digits=4, decimal_places=0, choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_TARIFA, True))
    producto = models.ForeignKey('ImpdProducto', db_column='id_producto')
    
    def str_tarifa(self):
        return '%.2f' % self.tarifa
    
    class Meta:
        db_table = 'impd_producto_impuesto'
        verbose_name = 'Impuesto de Producto'
        verbose_name_plural = 'Impuestos de Productos'

'''
----------------------------
GUIA DE REMISION
----------------------------
'''
class ImpdGuiaRemision(mixins.IMPDComprobanteMixin):
    ruc_empresa = models.ForeignKey('core.PorEmpresa', db_column='ruc_empresa')
    fecha_emision = models.DateField()
    
    direccion_partida = models.CharField(max_length=300)
    razon_social_transportista = models.CharField(max_length=300)
    tipo_identif_transportista = models.CharField(max_length=2, choices = P.TIPOS_IDENTIFICACION_TRANSP_CHOICES)#catalogo_helper.get_catalogo(P.CAT_TIPO_IDENTIFICACION))
    ruc_transportista = models.CharField(max_length=13)
    rise = models.CharField(max_length=40, blank=True)
    fecha_inicio_transporte = models.DateField()
    fecha_fin_transporte = models.DateField()
    placa = models.CharField(max_length=20)
    
    secuencial_number = models.IntegerField(default=0, blank=True)
    
    def get_fecha_emision(self):
        return self.fecha_emision.strftime("%d/%m/%Y")
    
    def get_destinatarios(self):
        destinatarios = ImpdGRDetalleDestinatario.objects.filter(guia_remision = self)
        return destinatarios
    
    def get_identificacion(self):
        destinatarios = ImpdGRDetalleDestinatario.objects.filter(guia_remision = self)
        if destinatarios.count() > 0:
            return destinatarios[0].destinatario.identificacion_destinatario
        return ""
    
    def get_razon_social(self):
        destinatarios = ImpdGRDetalleDestinatario.objects.filter(guia_remision = self)
        if destinatarios.count() > 0:
            return destinatarios[0].destinatario.razon_social_destinatario
        return ""

    def get_info_adicional(self):
        items = self.impdgrinformacionadicional_set.all()
        items = items.order_by('fecha_actualizacion').reverse()
        return items

    def __unicode__(self):
        return u'%d - %s' % (self.pk, self.secuencial)
    
    class Meta:
        db_table = 'impd_guia_remision'
        verbose_name = 'Guia de Remision Digital'
        verbose_name_plural = 'Guias de Remision Digitales' 

class ImpdGRDestinatario(mixins.AuditMixin):
    identificacion_destinatario = models.CharField(max_length=13)
    razon_social_destinatario = models.CharField(max_length=300)
    direccion_destinatario = models.CharField(max_length=300)    
    ruc_empresa = models.ForeignKey('core.PorEmpresa', db_column='ruc_empresa', related_name="destinatario_empresa")
    
    def __unicode__(self):
        return u'%s, %s' % (self.identificacion_destinatario, self.razon_social_destinatario)
    
    def get_descripcion(self):
        return '%s, %s' %\
            (self.identificacion_destinatario, self.razon_social_destinatario)
    
    class Meta:
        db_table = 'impd_gr_destinatario'
        verbose_name = 'Destinatario Guia de Remision'
        verbose_name_plural = 'Destinatarios Guias de Remision'

class ImpdGRDetalleDestinatario(mixins.AuditMixin):
    guia_remision = models.ForeignKey('ImpdGuiaRemision', db_column='id_guia_remision', related_name="detalle_destinatario_guia_remision")
    destinatario = models.ForeignKey('ImpdGRDestinatario', db_column='id_destinatario')
    motivo_traslado = models.CharField(max_length=300)
    documento_aduanero_unico = models.CharField(max_length=20, blank=True)
    codigo_establecimiento_destino = models.CharField(max_length=3, blank=True)
    ruta = models.CharField(max_length=300, blank=True)
    codigo_documento_sustento = models.CharField(max_length=2, choices = catalogo_helper.get_catalogo(P.CAT_TIPO_DOCUMENTO),  blank=True)
    num_documento_sustento = models.CharField(max_length=17, blank=True)
    num_autori_docum_sustento = models.CharField(max_length=37, blank=True)
    fecha_emi_docum_sustento = models.DateField()
    
    def get_productos_destinatario(self):
        destinatarios = ImpdGRProductoDestinatario.objects.filter(detalle_destinatario = self)
        return destinatarios
    
    class Meta:
        db_table = 'impd_gr_detalle_destinatario'
        verbose_name = 'Detalle Destinatario Guia Remision'
        verbose_name_plural = 'Detalles Destinatario Guia Remision'
        
class ImpdGRProductoDestinatario(mixins.AuditMixin):
    detalle_destinatario = models.ForeignKey('ImpdGRDetalleDestinatario', db_column='id_detalle_destinatario')
    producto = models.ForeignKey('ImpdProducto', db_column='id_producto')
    cantidad = models.DecimalField(max_digits=14, decimal_places=6, default=1)
    
    def str_cantidad(self):
        return '%.2f' % self.cantidad
    
    class Meta:
        db_table = 'impd_gr_producto_destinatario'
        verbose_name = 'Producto Destinatario Guia Remision'
        verbose_name_plural = 'Producto Destinatario Guia Remision'
        
class ImpdGRInformacionAdicional(mixins.AuditMixin):
    nombre = models.CharField(max_length=50)
    valor = models.CharField(max_length=300)
    guia_remision = models.ForeignKey('ImpdGuiaRemision', db_column='id_guia_remision')
    
    def __unicode__(self):
        return u'%s = %s' % (self.nombre, self.valor)
    
    class Meta:
        db_table = 'impd_gr_informacion_adicional'
        verbose_name = 'Informacion Adicional de Guia Remision'
        verbose_name_plural = 'Informaciones Adicionales de Guia Remision'

'''
----------------------------
COMPROBANTE DE RETENCION
----------------------------
'''
class ImpdComproRetencion(mixins.IMPDComprobanteMixin):
    ruc_empresa = models.ForeignKey('core.PorEmpresa', db_column='ruc_empresa')
    id_cliente = models.ForeignKey('ImpdCliente', db_column='id_cliente')
    fecha_emision = models.DateField()
    
    periodo_fiscal = models.CharField(max_length=7)
    secuencial_number = models.IntegerField(default=0, blank=True)
    
    def get_fecha_emision(self):
        return self.fecha_emision.strftime("%d/%m/%Y")

    def get_info_adicional(self):
        items = self.impdcretinformacionadicional_set.all()
        items = items.order_by('fecha_actualizacion').reverse()
        return items

    def get_impuestos(self):
        items = self.impdcretimpuestos_set.all()
        items = items.order_by('codigo_impuesto')
        return items
    
    def __unicode__(self):
        return u'%d - %s' % (self.pk, self.secuencial)
    
    class Meta:
        db_table = 'impd_compro_retencion'
        verbose_name = 'Comprobante de Retencion Digital'
        verbose_name_plural = 'Comprobantes de Retencion Digitales' 

class ImpdCRETImpuestos(mixins.AuditMixin):
    codigo_impuesto = models.CharField(max_length=1, choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_CODIGO_IMPUESTO))
    codigo_retencion = models.CharField(max_length=5, choices = catalogo_helper.get_catalogo(P.CAT_TABLA_19_RETENCION))
    base_imponible = models.DecimalField(max_digits=14, decimal_places=2)
    porcentaje_retener = models.CharField(max_length=6, choices = catalogo_helper.get_catalogo(P.CAT_TABLA_19_A_RETENCION,False), blank=True, default='5')
    porcentaje_retener_tmp = models.CharField(max_length=6, default='0', blank=True)
    valor_retenido = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_emi_docum_sustento = models.DateField()
    codigo_documento_sustento = models.CharField(max_length=2, choices = catalogo_helper.get_catalogo(P.CAT_TIPO_DOCUMENTO))
    numero_documento_sustento = models.CharField(max_length=15)
    compro_retencion = models.ForeignKey('ImpdComproRetencion', db_column='id_compro_retencion')
    
    def get_codigo_retencion(self):
        return self.codigo_retencion
    
    
    
    def __unicode__(self):
        return u'%s, %s' % (self.codigo_impuesto, self.codigo_retencion)
    
    class Meta:
        db_table = 'impd_cret_impuestos'
        verbose_name = 'Informacion Adicional de Retencion'
        verbose_name_plural = 'Informaciones Adicionales de Retencion'
    
    def save(self, *args, **kwargs):
        if self.codigo_retencion == 1 or not self.porcentaje_retener_tmp or self.porcentaje_retener_tmp == '0':
            self.porcentaje_retener_tmp = self.porcentaje_retener
            
        if self.codigo_retencion != 1:
            self.porcentaje_retener = self.porcentaje_retener_tmp
            
        super(ImpdCRETImpuestos, self).save(*args, **kwargs)

class ImpdCRETInformacionAdicional(mixins.AuditMixin):
    nombre = models.CharField(max_length=50)
    valor = models.CharField(max_length=300)
    compro_retencion = models.ForeignKey('ImpdComproRetencion', db_column='id_compro_retencion')
    
    def __unicode__(self):
        return u'%s = %s' % (self.nombre, self.valor)
    
    class Meta:
        db_table = 'impd_cret_informacion_adicional'
        verbose_name = 'Informacion Adicional de Retencion'
        verbose_name_plural = 'Informaciones Adicionales de Retencion'
        

'''
----------------------------
NOTA DE DEBITO
----------------------------
'''
class ImpdNotaDebito(mixins.IMPDComprobanteMixin):
    ruc_empresa = models.ForeignKey('core.PorEmpresa', db_column='ruc_empresa')
    id_cliente = models.ForeignKey('ImpdCliente', db_column='id_cliente')
    
    fecha_emision = models.DateField()
    codigo_documento_modificado = models.CharField(max_length=2, choices = catalogo_helper.get_catalogo(P.CAT_TIPO_DOCUMENTO))
    rise = models.CharField(max_length=40, blank=True)
    numero_documento_modificado  = models.CharField(max_length=17, blank=True)
    fecha_emision_documento_modificado = models.DateField()
    total_sin_impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    estado_pago = models.CharField(max_length=10, choices=P.ESTADO_PAGO_PAGADO_CHOICES, default=P.ESTADO_PAGO_PAGADO)
    secuencial_number = models.IntegerField(default=0, blank=True)
    
    def get_fecha_emision_documento_modificado(self):
        return self.fecha_emision_documento_modificado.strftime("%d/%m/%Y")
    
    def str_total_sin_impuestos(self):
        return '%.2f' % self.total_sin_impuestos
    
    def str_valor_total(self):
        return '%.2f' % self.valor_total
    
    def get_fecha_emision(self):
        return self.fecha_emision.strftime("%d/%m/%Y")

    def get_info_adicional(self):
        items = self.impdnotadebitoinfoadicional_set.all()
        items = items.order_by('fecha_actualizacion').reverse()
        return items

    class Meta:
        db_table = 'impd_nota_debito'
        verbose_name = 'Nota de Debito'
        verbose_name_plural = 'Notas de Debito'
    
class ImpdNotaDebitoImpuestos(mixins.AuditMixin):
    id_nota_debito = models.ForeignKey('ImpdNotaDebito', db_column='id_nota_debito')
    codigo_impuesto = models.CharField(max_length=2, choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_CODIGO_IMPUESTO))
    codigo_porcentaje = models.CharField(max_length=2, choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_CODIGO_PORCENTAJE))
    tarifa = models.DecimalField(max_digits=4, decimal_places=0, choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_TARIFA, True))
    base_imponible = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor = models.DecimalField(max_digits=14, decimal_places=2, default=0)
        
    def str_base_imponible(self):
        return '%.2f' % self.base_imponible
        
    def str_valor(self):
        return '%.2f' % self.valor
    
    class Meta:
        db_table = 'impd_nota_debito_impuestos'
        verbose_name = 'Impuesto de Nota de Debito'
        verbose_name_plural = 'Impuestos de Nota de Debito'

class ImpdNotaDebitoMotivos(mixins.AuditMixin):
    id_nota_debito = models.ForeignKey('ImpdNotaDebito', db_column='id_nota_debito')
    razon = models.CharField(max_length=300)
    valor = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'impd_nota_debito_motivos'
        verbose_name = 'Motivo de Nota de Debito'
        verbose_name_plural = 'Motivos de Nota de Debito'
    
class ImpdNotaDebitoInfoAdicional(mixins.AuditMixin):
    id_nota_debito = models.ForeignKey('ImpdNotaDebito', db_column='id_nota_debito')
    nombre = models.CharField(max_length=50)
    valor = models.CharField(max_length=300)
    
    class Meta:
        db_table = 'impd_nota_debito_informacion_adicional'
        verbose_name = 'Informacion Adicional de Nota de Debito'
        verbose_name_plural = 'Informaciones Adicionales de Nota de Debito'
    
'''
----------------------------
NUEVO: NOTA DE CREDITO
----------------------------
'''

class ImpdNotaCredito(mixins.IMPDComprobanteMixin):
    ruc_empresa = models.ForeignKey('core.PorEmpresa', db_column='ruc_empresa')
    id_cliente = models.ForeignKey('ImpdCliente', db_column='id_cliente')
    fecha_emision = models.DateField()
    rise = models.CharField(max_length=40)
    codigo_documento_modificado = models.CharField(max_length=2, choices = catalogo_helper.get_catalogo(P.CAT_TIPO_DOCUMENTO))
    numero_documento_modificado = models.CharField(max_length=17)
    fecha_emi_docum_sustento = models.DateField()
    motivo = models.CharField(max_length=64)
    total_sin_impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_modificacion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado_pago = models.CharField(max_length=10, choices=P.ESTADO_PAGO_PAGADO_CHOICES, default=P.ESTADO_PAGO_PAGADO)
    
    secuencial_number = models.IntegerField(default=0, blank=True)
    
    def str_total_sin_impuestos(self):
        return '%.2f' % self.total_sin_impuestos
    
    def str_valor_modificacion(self):
        return '%.2f' % self.valor_modificacion
    
    def get_fecha_emision(self):
        return self.fecha_emision.strftime("%d/%m/%Y")
    
    def get_fecha_emi_docum_sustento(self):
        #if self.fecha_emi_docum_sustento:
          #  self.fecha_emi_docum_sustento.strftime("%d/%m/%Y")
        return self.fecha_emi_docum_sustento.strftime("%d/%m/%Y")
    
    def get_impuestos_grouped(self):
        factura = ImpdNotaCredito.objects.get(pk = self.pk)
        items = factura.impditemnotacredito_set.all()
        impuestos = ImpdItemNotaCreditoImpuesto.objects.filter(id_item_nota_credito__in = items)\
            .values('producto_impuesto__codigo_impuesto','producto_impuesto__codigo_porcentaje','producto_impuesto__tarifa')\
            .annotate(valor = Sum('valor'), base_imponible = Sum('base_imponible'))
        return impuestos
    
    def get_subtotals_dict(self):
        subtotal12 = 0
        subtotal0 = 0
        subtotal_na = 0
        subtotal_ei = 0
        impuestos = self.get_impuestos_grouped()
        for totalConImp in impuestos:
            if totalConImp['producto_impuesto__codigo_porcentaje'] == '0':
                subtotal0 += float(totalConImp['base_imponible'])
            elif totalConImp['producto_impuesto__codigo_porcentaje'] == '2':
                subtotal12 += float(totalConImp['base_imponible'])
            elif totalConImp['producto_impuesto__codigo_porcentaje'] == '6':
                subtotal_na += float(totalConImp['base_imponible'])
            elif totalConImp['producto_impuesto__codigo_porcentaje'] == '7':
                subtotal_ei += float(totalConImp['base_imponible'])
        
        return {
            'subtotal12': '%.2f' % subtotal12,
            'subtotal0': '%.2f' % subtotal0,
            'subtotal_na': '%.2f' % subtotal_na,
            'subtotal_ei': '%.2f' % subtotal_ei,
        }

    def get_info_adicional(self):
        items = self.impdnotacreditoinformacionadicional_set.all()
        items = items.order_by('fecha_actualizacion').reverse()
        return items

    def get_totales(self):
        items = self.impditemnotacredito_set.all()
        total_sin_impuestos = 0
        total_impuestos = 0
        total_descuentos = 0
        
        for item in items:
            total_descuentos += float(item.descuento)
            subtotal = (float(item.cantidad) * float(item.id_producto.precio_unitario)) - float(item.descuento)
            impuestos_producto = float(item.id_producto.get_impuestos(subtotal))
            total_impuestos += impuestos_producto
            total_sin_impuestos += float(subtotal)
        
        return {
            'total_sin_impuestos':'%.2f' %total_sin_impuestos,
            'total_impuestos':'%.2f' %total_impuestos,
            'total_descuentos':'%.2f' %total_descuentos,
            'total':'%.2f' %(total_sin_impuestos + total_impuestos),
        }
    
    class Meta:
        db_table = 'impd_nota_credito'
        verbose_name = 'Nota Credito Digital'
        verbose_name_plural = 'Notas Credito Digitales'

class ImpdNotaCreditoInformacionAdicional(mixins.AuditMixin):
    nombre = models.CharField(max_length=50)
    valor = models.CharField(max_length=300)
    nota_credito = models.ForeignKey('ImpdNotaCredito', db_column='id_nota_credito')
    
    def __unicode__(self):
        return u'%s = %s' % (self.nombre, self.valor)
    
    class Meta:
        db_table = 'impd_nota_credito_informacion_adicional'
        verbose_name = 'Informacion Adicional de Nota Credito'
        verbose_name_plural = 'Informaciones Adicionales de Notas Credito'

class ImpdItemNotaCredito(mixins.AuditMixin):
    id_nota_credito = models.ForeignKey('ImpdNotaCredito', db_column='id_nota_credito')
    id_producto = models.ForeignKey('ImpdProducto', db_column='id_producto')
    cantidad = models.DecimalField(max_digits=14, decimal_places=6, default=1)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_sin_impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    def str_cantidad(self):
        return '%.2f' % self.cantidad
    
    def str_descuento(self):
        return '%.2f' % self.descuento
    
    def str_total_sin_impuestos(self):
        return '%.2f' % self.total_sin_impuestos
    
    def get_impuestos(self):
        impuestos = ImpdItemNotaCreditoImpuesto.objects.filter(id_item_nota_credito = self.pk)
        return impuestos
    
    class Meta:
        db_table = 'impd_item_nota_credito'
        verbose_name = 'Item Nota Credito Digital'
        verbose_name_plural = 'Items Nota Credito Digital'

class ImpdItemNotaCreditoImpuesto(mixins.AuditMixin):
    base_imponible = models.DecimalField(max_digits=14, decimal_places=2, default=1)
    valor = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    id_item_nota_credito = models.ForeignKey('ImpdItemNotaCredito', db_column='id_item_nota_credito')
    producto_impuesto = models.ForeignKey('ImpdProductoImpuesto', db_column='id_producto_impuesto')
    
    def str_base_imponible(self):
        return '%.2f' % self.base_imponible
    
    def str_valor(self):
        return '%.2f' % self.valor
    
    class Meta:
        db_table = 'impd_item_nota_credito_impuesto'
        verbose_name = 'Impuesto Item Nota Credito Digital'
        verbose_name_plural = 'Impuestos Items Nota Credito Digital'

'''
----------------------------
NUEVO-FIN: NOTA DE CREDITO
----------------------------
'''

class ImpdFactReembolso(mixins.AuditMixin):
    tipo_identificacion_proveedor_reembolso  = models.CharField(max_length=2,
                                                    choices = catalogo_helper.get_catalogo(P.CAT_TIPO_IDENTIFICACION))
    identificacion_proveedor_reembolso = models.CharField(max_length=20)
    cod_pais_pago_proveedor_reembolso = models.CharField(max_length=3,
                                                         choices = catalogo_helper.get_catalogo(P.CAT_EXP_PAISES))
    tipo_proveedor_reembolso = models.CharField(max_length=3,
                                                choices = catalogo_helper.get_catalogo(P.CAT_TIPO_PROV_REEMBOLSO))
    cod_doc_reembolso = models.CharField(max_length=2, choices = catalogo_helper.get_catalogo(P.CAT_TIPO_DOCUMENTO))
    estab_doc_reembolso = models.CharField(max_length=3)
    pto_emi_doc_reembolso = models.CharField(max_length=3)
    secuencial_doc_reembolso = models.CharField(max_length=9)
    fecha_emision = models.CharField(max_length=10)
    numero_autorizacion = models.CharField(max_length=37)

    factura = models.ForeignKey('ImpdFactura', db_column='id_factura')

    def __unicode__(self):
        return u'%s = %s' % (self.identificacion_proveedor_reembolso, self.secuencial_doc_reembolso)

    class Meta:
        db_table = 'impd_fact_reembolso'
        verbose_name = 'Reemboso de Factura'
        verbose_name_plural = 'Reembolsos de Facturas'

class ImpdFactDetalleImpuestoReembolso(mixins.AuditMixin):
    codigo_reembolso = models.CharField(max_length=3,
                            choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_REEM_CODIGO_REEMBOLSO))
    codigo_porcentaje_rembolso = models.CharField(max_length=4,
                            choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_REEM_CODIGO_PORCENTAJE))
    tarifa_reembolso = models.CharField(max_length=4,
                            choices = catalogo_helper.get_catalogo(P.CAT_DETALLE_IMPUESTO_REEM_TARIFA))
    base_imponible_reembolso = models.DecimalField(max_digits=14, decimal_places=2)
    impuesto_reembolso = models.DecimalField(max_digits=14, decimal_places=2)

    reembolso = models.ForeignKey('ImpdFactReembolso', db_column='id_reembolso')

    class Meta:
        db_table = 'impd_fact_detalle_impuesto'
        verbose_name = 'Impuesto de Reemboso'
        verbose_name_plural = 'Impuestos de Reembolsos'

class ImpdFactPago(mixins.AuditMixin):
    forma_pago = models.CharField(max_length=2, choices = catalogo_helper.get_catalogo(P.CAT_FORMA_PAGO))
    total = models.DecimalField(max_digits=14, decimal_places=2)
    plazo = models.CharField(max_length=8)
    unidad_tiempo = models.CharField(max_length=10, choices = catalogo_helper.get_catalogo(P.CAT_UNIDAD_TIEMPO))

    factura = models.ForeignKey('ImpdFactura', db_column='id_factura')

    class Meta:
        db_table = 'impd_fact_pago'
        verbose_name = 'Pago de Factura'
        verbose_name_plural = 'Pagos de Facturas'
