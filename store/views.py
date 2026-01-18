from django.shortcuts import render, get_object_or_404
from .models import Mystery_Box
from .models import *
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .forms import ProductoForm, CajaForm #imprtamos el form que hicimos

# Create your views here.
def home(request):
    cajitas= Mystery_Box.objects.all()
    return render(request, "store/templates/home.html", {'boxes' : cajitas}) 
    #funcion render


def box(request, id): #COMO LAS CAJAS RECIBEN UN ID PARA VER QUE HACER CON EL HTML PONEMOS ACA EL ID
    box = get_object_or_404(Mystery_Box, id=id)
    return render(request, "store/templates/detalle_caja.html", {'caja' : box})
    
class CajaCreateView(LoginRequiredMixin, CreateView, PermissionRequiredMixin): #TODO al crear que mande a un mensaje de exito

    model = Mystery_Box
    form_class = CajaForm
    template_name = 'store/templates/CajaUpdateCreateView.html'
    success_url = reverse_lazy('home')


class CajaUpdateView(LoginRequiredMixin, UpdateView, PermissionRequiredMixin): 
    model = Mystery_Box
    form_class = CajaForm
    template_name = 'store/templates/CajaUpdateCreateView.html'
    success_url = reverse_lazy('home')


def simulacion(request):
    pass

def compra_exitosa(request, id):
    box = get_object_or_404(Mystery_Box, id=id)
    return render(request, "store/templates/pago_exitoso.html", {'caja' : box})

class ProductoListView(LoginRequiredMixin, ListView): 
    queryset = Producto.objects.prefetch_related('categoria') #prefetch related es para many to many
    template_name = 'store/templates/ProductoListView.html'
    context_object_name = 'productos'
    #TODO paginacion paginate_by = 10

class ProductoCreateView(LoginRequiredMixin, CreateView, PermissionRequiredMixin):
    model = Producto
    form_class = ProductoForm
    template_name = 'store/templates/ProductoCreateView.html'
    success_url = reverse_lazy('productos')
    #Todo permission_required = 1231

class ProductoUpdateView(LoginRequiredMixin, UpdateView, PermissionRequiredMixin):
    model = Producto #todo revisar que pasa si a un producto que ya esta en una categoria, en una caja, comprado le cambio su
    #categoria
    form_class = ProductoForm
    template_name = 'store/templates/ProductoUpdateView.html'
    success_url = reverse_lazy('productos')
    #Todo permission_required = 1231