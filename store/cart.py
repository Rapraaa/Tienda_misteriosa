from decimal import Decimal
from .models import Mystery_Box, CarritoItem


class Cart:
    #    Clase para manejar el carrito de compras.
    #! Para usuarios anónimos: usa session
    #!Para usuarios autenticados: usa el modelo CarritoItem

    def __init__(self, request):
        self.request = request
        self.session = request.session

        if not request.user.is_authenticated:
            # Para usuarios anónimos, usamos la sesión
            cart = self.session.get("cart")
            if not cart:
                cart = self.session["cart"] = {}
            self.cart = cart
        else:
            # Para usuarios autenticados, usamos la base de datos
            self.cart = None

    def add(self, caja_id, cantidad=1):
        # agregar cjaa
        caja_id = str(caja_id)

        if self.request.user.is_authenticated:
            # Usuario autenticado: guardar en DB
            try:
                caja = Mystery_Box.objects.get(id=caja_id)
                carrito_item, created = CarritoItem.objects.get_or_create(
                    usuario=self.request.user,
                    caja=caja,
                    defaults={"cantidad": cantidad},
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
        # eliminar caja de un carrito
        caja_id = str(caja_id)

        if self.request.user.is_authenticated:
            # Usuario autenticado: eliminar de DB
            CarritoItem.objects.filter(
                usuario=self.request.user, caja_id=caja_id
            ).delete()
        else:
            # Usuario anónimo: eliminar de sesión
            if caja_id in self.cart:
                del self.cart[caja_id]
                self.save()

    def clear(self):
        # vaciar el carrito
        if self.request.user.is_authenticated:
            CarritoItem.objects.filter(usuario=self.request.user).delete()
        else:
            self.session["cart"] = {}
            self.save()

    def get_items(self):

        # guarda los items en un json
        items = []

        if self.request.user.is_authenticated:
            # Usuario autenticado: obtener de DB
            carrito_items = CarritoItem.objects.filter(
                usuario=self.request.user
            ).select_related("caja")

            for item in carrito_items:
                items.append(
                    {
                        "caja": item.caja,
                        "cantidad": item.cantidad,
                        "subtotal": item.subtotal,
                    }
                )
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

                items.append({"caja": caja, "cantidad": cantidad, "subtotal": subtotal})

        return items

    def get_coupon(self):
        coupon_code = self.session.get("coupon_code")
        if coupon_code:
            from .models import Cupon

            try:
                return Cupon.objects.get(codigo=coupon_code)
            except Cupon.DoesNotExist:
                return None
        return None

    def get_discount(self):
        coupon = self.get_coupon()
        if coupon:
            subtotal = self.get_subtotal()
            return coupon.calcular_descuento(subtotal)
        return Decimal("0.00")

    def get_total(self):
        # total del carrito
        subtotal = self.get_subtotal() - self.get_discount()
        if subtotal < Decimal("0.00"):
            subtotal = Decimal("0.00")
        from .models import Configuracion

        tasa_iva = Configuracion.get_iva()

        impuesto = subtotal * (tasa_iva / Decimal(100))
        total = subtotal + impuesto
        return total.quantize(Decimal("0.01"))

    def get_subtotal(self):
        # subtotal, sim iva
        items = self.get_items()
        return sum(item["subtotal"] for item in items)

    def get_iva_amount(self):
        # monto total de iva calculada
        subtotal = self.get_subtotal() - self.get_discount()
        if subtotal < Decimal("0.00"):
            subtotal = Decimal("0.00")
        from .models import Configuracion

        tasa_iva = Configuracion.get_iva()
        return (subtotal * (tasa_iva / Decimal(100))).quantize(Decimal("0.01"))

    def get_iva_percentage(self):
        # el iva
        from .models import Configuracion

        return Configuracion.get_iva()

    def get_count(self):
        # sumamos la cantidad de items
        if self.request.user.is_authenticated:
            from django.db.models import Sum

            return (
                CarritoItem.objects.filter(usuario=self.request.user).aggregate(
                    total=Sum("cantidad")
                )["total"]
                or 0
            )
        else:
            return sum(self.cart.values())

    def merge_to_user(self, user):
        # mezvcla los carritos

        if not self.session.get("cart"):
            return

        for caja_id, cantidad in self.session["cart"].items():
            try:
                caja = Mystery_Box.objects.get(id=caja_id)
                carrito_item, created = CarritoItem.objects.get_or_create(
                    usuario=user, caja=caja, defaults={"cantidad": cantidad}
                )
                if not created:
                    # si ya tenia desde antes carritos, se suman
                    carrito_item.cantidad += cantidad
                    carrito_item.save()
            except Mystery_Box.DoesNotExist:
                continue

        # limpiamos el carrito
        self.session["cart"] = {}
        self.save()

    def save(self):
        # debemos avisar que modificamos la sesion, para que guarde
        self.session.modified = True

    def apply_coupon(self, code):
        self.session["coupon_code"] = code
        if "descuento" in self.session:
            del self.session["descuento"]
        self.save()

    def remove_coupon(self):
        if "coupon_code" in self.session:
            del self.session["coupon_code"]
            self.save()
