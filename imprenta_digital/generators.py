# -*- coding: utf-8 -*-
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse
from django.conf import settings

import os
import ho.pisa as pisa
import cStringIO as StringIO
import cgi

class PDFGenerator(object):
    '''
    PDFGenerator
    @description    Permite generar pdfs a partir de html procesado en base a los parametros pasados a esta clase
    @author         jimbuho
    @version        1.0
    '''
    def __init__(self, template_name, pdf_model=None, pdf_model_id=None, pagesize='A4', entities={}):
        self.template_name = template_name
        self.entities = entities
        if pdf_model and pdf_model_id:
            self.entities['item'] = get_object_or_404(pdf_model, pk=pdf_model_id)
        self.pagesize = pagesize
        
    def build_context(self):
        ctx = {}
        ctx['pagesize'] = self.pagesize
        for k,v in self.entities.items():
            ctx[k] = v
        return ctx
    
    def process(self, request):
        html = render_to_string(self.template_name, self.build_context(), context_instance=RequestContext(request))
        return self.generate_pdf(html)

    def generate_pdf(self, html):
        # Funcion para generar el archivo PDF y devolverlo mediante HttpResponse
        result = StringIO.StringIO()
        pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("UTF-8")), dest=result, link_callback=self.fetch_resources)
        if not pdf.err:
            return HttpResponse(result.getvalue(), mimetype='application/pdf')
        return HttpResponse('Error al generar el PDF: %s' % cgi.escape(html))
    
    def fetch_resources(self, uri, rel):
        # Funcion para corregir la URL de archivos multimedia insertados en el documento
        try:
            new_uri = uri.replace(settings.MEDIA_URL, "")
            path = os.path.join(settings.MEDIA_ROOT, new_uri)
        except Exception as e:
            print e
        return path
    