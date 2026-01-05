from django.shortcuts import render, get_object_or_404
from .models import Mystery_Box

# Create your views here.
def home(request):
    cajitas= Mystery_Box.objects.all()
    return render(request, "store/templates/home.html", {'boxes' : cajitas}) 
    #funcion render


def box(request, id): #COMO LAS CAJAS RECIBEN UN ID PARA VER QUE HACER CON EL HTML PONEMOS ACA EL ID
    box = get_object_or_404(Mystery_Box, id=id)
    return render(request, "store/templates/detalle_caja.html", {'caja' : box})


def simulacion(request):
    pass

def compra_exitosa(request, id):
    box = get_object_or_404(Mystery_Box, id=id)
    return render(request, "store/templates/pago_exitoso.html", {'caja' : box})