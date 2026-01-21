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
    
    # Carrito de compras
    path('carrito/', ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:id>/', agregar_al_carrito, name='agregar_carrito'),
    path('carrito/eliminar/<int:id>/', eliminar_del_carrito, name='eliminar_carrito'),
    path('carrito/checkout/', checkout_carrito, name='checkout_carrito'),
    path('carrito/compra-exitosa/', compra_exitosa_carrito, name='compra_exitosa_carrito'),
    
    # Cupones
    path('cupon/validar/', validar_cupon, name='validar_cupon'),
    path('cupon/remover/', remover_cupon, name='remover_cupon'),
    
    # Gestión de Cupones
    path('cupones/', CuponListView.as_view(), name='cupones_lista'),
    path('cupones/crear/', CuponCreateView.as_view(), name='cupon_crear'),
    path('cupones/<int:pk>/', CuponDetailView.as_view(), name='cupon_detalle'),
    path('cupones/<int:pk>/editar/', CuponUpdateView.as_view(), name='cupon_editar'),
    path('cupones/<int:pk>/eliminar/', CuponDeleteView.as_view(), name='cupon_eliminar'),
    
    # Logs de Auditoría
    path('sistema/logs/', AuditLogView.as_view(), name='audit_log'),
    
    # Administración de Usuarios
    path('gestion/usuarios/', UserListView.as_view(), name='admin_users_list'),
    path('gestion/usuarios/<int:pk>/editar/', UserUpdateView.as_view(), name='admin_users_edit'),
    path('gestion/usuarios/<int:pk>/historial/', UserDetailView.as_view(), name='admin_users_detail'),
]
#todo enviar correo con el numero guia, o en la misma pagina
