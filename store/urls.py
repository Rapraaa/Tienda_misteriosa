from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views


urlpatterns = [ 
    path("", home, name="home"),
    path("caja/<int:id>/", box, name="box"),
    path("caja/<int:id>/comprar", simulacion, name="simulacion"),
    path("compra-exitosa/<int:id>/", compra_exitosa,name='compra_exitosa' ),
    path("productos/", ProductoListView.as_view(), name='productos'),
    path('productos/nuevo/', ProductoCreateView.as_view(), name='crear_productos'),
    path('producto/editar/<int:pk>', ProductoUpdateView.as_view(), name='editar_producto'), #EN MIXINS ES PK NO ID
    path('caja/nuevo/', CajaCreateView.as_view(), name='crear_caja'),
    path('caja/editar/<int:pk>', CajaUpdateView.as_view(), name='editar_caja'),
]