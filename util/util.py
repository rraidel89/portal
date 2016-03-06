from django.shortcuts import get_object_or_404
from django.views.generic.base import View
from wkhtmltopdf.views import PDFTemplateResponse
from core.models import Cupon

__author__ = 'alfredo'


class MyPDFView(View):
    template = 'emisores/cupon-pdf.html'

    def get(self, request, *args, **kwargs):
        response = PDFTemplateResponse(request=request,
                                       template=self.template,
                                       filename="cupon-descuento.pdf",
                                       context=self.get_context_data(),
                                       show_content_in_browser=False,
                                       cmd_options={'margin-top': 10},
        )
        return response

    def get_context_data(self):
        return {
            "form_cupon": self.get_object(),
        }

    def get_object(self):
        return get_object_or_404(Cupon, pk=self.kwargs.get("id_cupon"))


def leer_desde_txt():
    with open('media/mensajes.txt', 'r') as f:
        my_names = [line.strip() for line in f]
        print '---'
    for item in my_names:
        print item
    return my_names


from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class LoggedInMixin(object):
    """clase auxilar utilizada en las cbv para determinar si usuario esta logueado"""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoggedInMixin, self).dispatch(*args, **kwargs)