from decimal import Decimal
from .models import Mystery_Box, CarritoItem

class Cart:
    """
    Clase para manejar el carrito de compras.
    - Para usuarios anónimos: usa session
    - Para usuarios autenticados: usa el modelo CarritoItem
    """
    
    def __init__(self, request):
        self.request = request
        self.session = request.session
        
        if not request.user.is_authenticated:
            # Para usuarios anónimos, usamos la sesión
            cart = self.session.get('cart')
            if not cart:
                cart = self.session['cart'] = {}
            self.cart = cart
        else:
            # Para usuarios autenticados, usamos la base de datos
            self.cart = None
    
    def add(self, caja_id, cantidad=1):
        """Agrega una caja al carrito"""
        caja_id = str(caja_id)
        
        if self.request.user.is_authenticated:
            # Usuario autenticado: guardar en DB
            try:
                caja = Mystery_Box.objects.get(id=caja_id)
                carrito_item, created = CarritoItem.objects.get_or_create(
                    usuario=self.request.user,
                    caja=caja,
                    defaults={'cantidad': cantidad}
                )
                if not created:
                    # Si ya existe, incrementar cantidad
                    carrito_item.cantidad += cantidad
                    carrito_item.save()
            except Mystery_Box.DoesNotExist:
                pass
        else:
            # Usuario anónimo: guardar en sesión
            if caja_id in self.cart:
                self.cart[caja_id] += cantidad
            else:
                self.cart[caja_id] = cantidad
            self.save()
    
    def remove(self, caja_id):
        """Elimina una caja del carrito"""
        caja_id = str(caja_id)
        
        if self.request.user.is_authenticated:
            # Usuario autenticado: eliminar de DB
            CarritoItem.objects.filter(
                usuario=self.request.user,
                caja_id=caja_id
            ).delete()
        else:
            # Usuario anónimo: eliminar de sesión
            if caja_id in self.cart:
                del self.cart[caja_id]
                self.save()
    
    def clear(self):
        """Vacía el carrito completamente"""
        if self.request.user.is_authenticated:
            CarritoItem.objects.filter(usuario=self.request.user).delete()
        else:
            self.session['cart'] = {}
            self.save()
    
    def get_items(self):
        """
        Retorna lista de items del carrito con formato:
        [{'caja': Mystery_Box, 'cantidad': int, 'subtotal': Decimal}, ...]
        """
        items = []
        
        if self.request.user.is_authenticated:
            # Usuario autenticado: obtener de DB
            carrito_items = CarritoItem.objects.filter(
                usuario=self.request.user
            ).select_related('caja')
            
            for item in carrito_items:
                items.append({
                    'caja': item.caja,
                    'cantidad': item.cantidad,
                    'subtotal': item.subtotal
                })
        else:
            # Usuario anónimo: obtener de sesión
            from .utils import es_usuario_premium
            es_premium = es_usuario_premium(self.request.user)
            
            caja_ids = self.cart.keys()
            cajas = Mystery_Box.objects.filter(id__in=caja_ids)
            
            for caja in cajas:
                cantidad = self.cart[str(caja.id)]
                precio = caja.precio_suscripcion if es_premium else caja.precio_base
                subtotal = precio * cantidad
                
                items.append({
                    'caja': caja,
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })
        
        return items
    
    def get_total(self):
        """Retorna el total del carrito"""
        items = self.get_items()
        return sum(item['subtotal'] for item in items)
    
    def get_count(self):
        """Retorna el número total de items en el carrito"""
        if self.request.user.is_authenticated:
            return CarritoItem.objects.filter(usuario=self.request.user).count()
        else:
            return len(self.cart)
    
    def merge_to_user(self, user):
        """
        Migra el carrito de sesión a la base de datos cuando el usuario inicia sesión.
        Se llama después del login.
        """

        if not self.session.get('cart'):
            return
        
        for caja_id, cantidad in self.session['cart'].items():
            try:
                caja = Mystery_Box.objects.get(id=caja_id)
                carrito_item, created = CarritoItem.objects.get_or_create(
                    usuario=user,
                    caja=caja,
                    defaults={'cantidad': cantidad}
                )
                if not created:
                    # Si ya tenía items en su carrito, sumar cantidades
                    carrito_item.cantidad += cantidad
                    carrito_item.save()
            except Mystery_Box.DoesNotExist:
                continue
        
        # Limpiar el carrito de sesión
        self.session['cart'] = {}
        self.save()
    
    def save(self):
        """Marca la sesión como modificada para que Django la guarde"""
        self.session.modified = True
