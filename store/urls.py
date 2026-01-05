from django.urls import path
from .views import *

urlpatterns = [ 
    path("", home, name="home"),
    path("caja/<int:id>/", box, name="box"),
    path("caja/<int:id>/comprar", simulacion, name="simulacion"),
    path("compra-exitosa/<int:id>/", compra_exitosa,name='compra_exitosa' )
]