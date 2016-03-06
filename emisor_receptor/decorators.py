from django.core.urlresolvers import reverse 
from django.http import HttpResponseRedirect, HttpResponse

def profile_required(view_func): 
    def _wrapped_view_func(request, *args, **kwargs):
        try:
            profile = request.user.get_profile()
        except:
            return HttpResponse("Se requiere un usuario con perfil para el ingreso a esta zona de Innobee")
        return view_func(request, *args, **kwargs) 
    return _wrapped_view_func

def enterprise_profile_required(view_func): 
    def _wrapped_view_func(request, *args, **kwargs):
        try:
            if not request.user.get_profile().ruc_empresa:
                return HttpResponse("Esta zona de Innobee es restringida")
        except:
            return HttpResponse("Esta zona de Innobee es restringida")
        return view_func(request, *args, **kwargs) 
    return _wrapped_view_func

