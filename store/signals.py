from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .cart import Cart

@receiver(user_logged_in)
def merge_cart_on_login(sender, user, request, **kwargs):
    """
    Señal que se ejecuta cuando un usuario inicia sesión.
    Carga el carrito de la sesión y lo fusiona con el carrito guardado en base de datos.
    """
    if request:
        cart = Cart(request)
        cart.merge_to_user(user)
