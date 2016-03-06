from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

import forms
import datetime

class IMPDCreateViewMixin(CreateView):
    
    def __init__(self, description):
        self.description = description
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(IMPDCreateViewMixin, self).dispatch(*args, **kwargs)
    
    def get_current_empresa(self):
        empresa = None
        try:
            empresa = self.request.user.get_profile().ruc_empresa
        except Exception as e:
            print 'get_current_empresa - Error:', e
        return empresa

    def get_context_data(self, **kwargs):
        ctx = super(IMPDCreateViewMixin, self).get_context_data(**kwargs)
        ctx['configuracion_form'] = forms.ConfiguracionFacturaForm(initial=
            {'descripcion':self.description, 'ruc_empresa': self.get_current_empresa()})
        ctx['empresa'] = self.get_current_empresa()
        return ctx
    
    def get_initial(self):
        return {'ruc_empresa': self.get_current_empresa(), 'fecha_emision':datetime.date.today(),
                'descripcion':'Facturas'}

class IMPDUpdateViewMixin(UpdateView):
    
    def __init__(self, description):
        self.description = description

    def get_current_empresa(self):
        empresa = None
        try:
            empresa = self.request.user.get_profile().ruc_empresa
        except Exception as e:
            print 'get_current_empresa - Error:', e
        return empresa

    def get_context_data(self, **kwargs):
        ctx = super(IMPDUpdateViewMixin, self).get_context_data(**kwargs)
        ctx['empresa'] = self.get_current_empresa()
        self.request.session['updated-entity'] = self.object
        return ctx
    