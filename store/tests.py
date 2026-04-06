# store/tests.py
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import json
import stripe
from unittest.mock import patch

from .models import (
    Mystery_Box,
    Producto,
    Suscripcion,
    Envio,
    Categoria,
    Cupon,
    Configuracion,
)
from .utils import generar_caja
from .cart import Cart


class AlgoritmoCajaTest(TestCase):
    def setUp(self):
        # 1. Crear Usuario
        self.user = User.objects.create_user(username="rapra_tester", password="123")

        # 2. Crear Categorías
        self.cat_anime = Categoria.objects.create(nombre="Anime")
        self.cat_relleno = Categoria.objects.create(nombre="Cocina")

        # 3. Crear Caja
        self.caja_otaku = Mystery_Box.objects.create(
            nombre="Caja Otaku",
            precio_base=Decimal("20.00"),
            descripcion="Caja de prueba",
        )
        self.caja_otaku.allowed_categories.add(self.cat_anime)

    def test_generar_caja_escenario_ideal(self):
        # Crear 5 productos de Anime
        for i in range(5):
            p = Producto.objects.create(
                nombre=f"Figura Naruto {i}", valor=Decimal("5.00"), stock=10
            )
            p.categoria.add(self.cat_anime)

        # Usar usuario y caja en vez de suscripcion
        envio = Envio.objects.create(
            usuario=self.user,
            caja=self.caja_otaku,
            estado="P",
            valor_total=Decimal("20.00"),
        )
        generar_caja(envio)

        # Verificaciones
        self.assertEqual(envio.productos.count(), 3)
        for prod in envio.productos.all():
            self.assertTrue(prod.categoria.filter(id=self.cat_anime.id).exists())

        # Verify financial tracking updates
        self.assertEqual(envio.valor_pagado, envio.valor_total)
        self.assertEqual(envio.costo_contenido, Decimal("15.00"))  # 3 products * 5.00

    def test_generar_caja_con_relleno_forzoso(self):
        # 1 producto de Anime
        p1 = Producto.objects.create(nombre="Manga Solo", valor=Decimal("5.00"))
        p1.categoria.add(self.cat_anime)

        # 5 productos de Cocina (Relleno)
        for i in range(5):
            p_relleno = Producto.objects.create(
                nombre=f"Cuchara {i}", valor=Decimal("2.00")
            )
            p_relleno.categoria.add(self.cat_relleno)

        envio = Envio.objects.create(
            usuario=self.user,
            caja=self.caja_otaku,
            estado="P",
            valor_total=Decimal("20.00"),
        )
        generar_caja(envio)

        self.assertEqual(envio.productos.count(), 3)
        nombres = [p.nombre for p in envio.productos.all()]
        self.assertIn("Manga Solo", nombres)
        # Cost check
        self.assertEqual(envio.valor_pagado, envio.valor_total)
        self.assertEqual(envio.costo_contenido, Decimal("9.00"))  # 5 + 2 + 2

    def test_filtro_de_presupuesto(self):
        # Producto Caro ($100)
        p_caro = Producto.objects.create(nombre="Estatua Oro", valor=Decimal("100.00"))
        p_caro.categoria.add(self.cat_anime)

        # Productos Baratos ($5)
        for i in range(3):
            p_barato = Producto.objects.create(
                nombre=f"Llavero {i}", valor=Decimal("5.00")
            )
            p_barato.categoria.add(self.cat_anime)

        envio = Envio.objects.create(
            usuario=self.user,
            caja=self.caja_otaku,
            estado="P",
            valor_total=Decimal("20.00"),
        )
        generar_caja(envio)

        self.assertEqual(envio.productos.count(), 3)
        nombres = [p.nombre for p in envio.productos.all()]
        self.assertNotIn("Estatua Oro", nombres)


class CartCouponTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="cart_tester", password="123")
        Configuracion.objects.create(id=1, tasa_iva=Decimal("15.00"))

        self.caja = Mystery_Box.objects.create(
            nombre="Caja Test",
            precio_base=Decimal("100.00"),
            descripcion="Caja de prueba",
        )

        # Valid coupon
        self.cupon = Cupon.objects.create(
            codigo="DESC10",
            descuento_fijo=Decimal("10.00"),
            activo=True,
            fecha_inicio=timezone.now() - timedelta(days=1),
            fecha_expiracion=timezone.now() + timedelta(days=1),
            monto_minimo=Decimal("50.00"),
        )

        # Session mock
        self.session = {}

    def get_mock_request(self, user=None):
        request = self.factory.get("/")
        request.user = user if user else self.user
        request.session = self.session
        return request

    def test_dynamic_cart_coupon_calculation(self):
        request = self.get_mock_request(user=self.user)
        cart = Cart(request)
        cart.add(self.caja.id, cantidad=1)

        subtotal = cart.get_subtotal()
        self.assertEqual(subtotal, Decimal("100.00"))

        # Apply coupon
        request.session["coupon_code"] = "DESC10"

        # Check discount
        discount = cart.get_discount()
        self.assertEqual(discount, Decimal("10.00"))

        # Total should be (100 - 10) * 1.15 = 103.50
        total = cart.get_total()
        self.assertEqual(total, Decimal("103.50"))


class StripeWebhookTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="stripe_tester", password="123")
        Configuracion.objects.create(id=1, tasa_iva=Decimal("15.00"))

        self.caja = Mystery_Box.objects.create(
            nombre="Caja Webhook",
            precio_base=Decimal("50.00"),
            descripcion="Caja para webhook",
        )

    @patch("store.views.stripe.Webhook.construct_event")
    def test_stripe_webhook_fulfillment_unica(self, mock_construct_event):
        # Mock the event payload for 'checkout.session.completed'
        mock_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "payment_status": "paid",
                    "client_reference_id": str(self.user.id),
                    "metadata": {"tipo_compra": "unica", "caja_id": self.caja.id},
                    "shipping_details": {
                        "name": "Test User",
                        "address": {
                            "line1": "123 Test St",
                            "city": "Test City",
                            "country": "EC",
                            "postal_code": "12345",
                        },
                    },
                }
            },
        }
        mock_construct_event.return_value = mock_event

        request = self.factory.post(
            "/stripe_webhook/", "{}", content_type="application/json"
        )
        request.META["HTTP_STRIPE_SIGNATURE"] = "test_sig"

        # Test needs setting STRIPE_WEBHOOK_SECRET temporarily
        with patch("store.views.getattr") as mock_getattr:
            mock_getattr.return_value = "whsec_test"
            from store.views import stripe_webhook

            response = stripe_webhook(request)

        self.assertEqual(response.status_code, 200)

        # Assert Envio was created
        envio = Envio.objects.get(stripe_session_id="cs_test_123")
        self.assertEqual(envio.usuario, self.user)
        self.assertEqual(envio.caja, self.caja)
        self.assertEqual(envio.estado, "P")

    @patch("store.views.stripe.Webhook.construct_event")
    def test_stripe_webhook_unpaid(self, mock_construct_event):
        mock_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_unpaid",
                    "payment_status": "unpaid",
                    "client_reference_id": str(self.user.id),
                }
            },
        }
        mock_construct_event.return_value = mock_event

        request = self.factory.post(
            "/stripe_webhook/", "{}", content_type="application/json"
        )
        request.META["HTTP_STRIPE_SIGNATURE"] = "test_sig"

        with patch("store.views.getattr") as mock_getattr:
            mock_getattr.return_value = "whsec_test"
            from store.views import stripe_webhook

            response = stripe_webhook(request)

        self.assertEqual(response.status_code, 200)
        # Should not create Envio because payment_status is 'unpaid'
        self.assertEqual(
            Envio.objects.filter(stripe_session_id="cs_test_unpaid").count(), 0
        )
