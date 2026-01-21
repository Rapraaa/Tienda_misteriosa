from django import template
from store.cart import Cart

register = template.Library()

@register.simple_tag
def cart_count(request):
    """Retorna el número de items en el carrito"""
    cart = Cart(request)
    return cart.get_count()
