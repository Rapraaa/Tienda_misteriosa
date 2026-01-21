from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views


urlpatterns = [ 
    path("", home, name="home"),
    path("caja/<int:id>/", box, name="box"),
    path("caja/<int:id>/comprar", crear_checkout_session, name="simulacion"),
    path("compra-exitosa/<int:id>/", compra_exitosa,name='compra_exitosa' ),
    path("productos/", ProductoListView.as_view(), name='productos'),
    path('productos/nuevo/', ProductoCreateView.as_view(), name='crear_productos'),
    path('producto/editar/<int:pk>', ProductoUpdateView.as_view(), name='editar_producto'), #EN MIXINS ES PK NO ID
    path('categorias/', CategoriaListView.as_view(), name='categorias'),
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='crear_categoria'),
    path('categorias/editar/<int:pk>/', CategoriaUpdateView.as_view(), name='editar_categoria'),
    path('categorias/toggle/<int:pk>/', categoria_toggle_activa, name='toggle_categoria'),
    path('caja/nuevo/', CajaCreateView.as_view(), name='crear_caja'),
    path('caja/editar/<int:pk>', CajaUpdateView.as_view(), name='editar_caja'),
    path('suscripciones/', SuscripcionListView.as_view(), name='suscripciones'),
    path('checkout/<int:id>/', crear_checkout_session, name='checkout'),
    path('compra-exitosa/<int:id>/', compra_exitosa, name='compra_exitosa'),
    path('envios/', EnviosListView.as_view(), name='envios'),
    path('despachar/<int:pk>/', EnviosUpdateView.as_view(), name='despachar_envio'),
    path('rastreo/', rastrear_pedido, name='rastrear_pedido'),
    path('perfil/', perfil, name='perfil'),
    path('suscribirse/premium/', crear_suscripcion_premium, name='suscribirse_premium'),
    path('membresia-exitosa/', membresia_exitosa, name='membresia_exitosa'),

]
#todo enviar correo con el numero guia, o en la misma pagina