# store/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Mystery_Box, Producto, Suscripcion, Envio, Categoria
from .utils import generar_caja

class AlgoritmoCajaTest(TestCase):

    def setUp(self):
        # 1. Crear Usuario
        self.user = User.objects.create_user(username='rapra_tester', password='123')
        
        # 2. Crear Categorías
        self.cat_anime = Categoria.objects.create(nombre="Anime")
        self.cat_relleno = Categoria.objects.create(nombre="Cocina")

        # 3. Crear Caja (Sin categorías aún)
        self.caja_otaku = Mystery_Box.objects.create(
            nombre="Caja Otaku",
            monthly_price=Decimal('20.00'),
            descripcion="Caja de prueba"
        )
        # Asignar ManyToMany
        self.caja_otaku.allowed_categories.add(self.cat_anime)

        # 4. Crear Suscripción
        self.suscripcion = Suscripcion.objects.create(
            usuario=self.user,
            caja=self.caja_otaku,
            estado='A'
        )

    def test_generar_caja_escenario_ideal(self):
        # Crear 5 productos de Anime
        for i in range(5):
            p = Producto.objects.create(
                nombre=f"Figura Naruto {i}", # 'nombre' según tu modelo
                valor=Decimal('5.00'),       # 'valor' según tu modelo
                stock=10
            )
            p.categoria.add(self.cat_anime) # ManyToMany

        envio = Envio.objects.create(suscripcion=self.suscripcion, estado='P')
        generar_caja(envio)

        # Verificaciones
        self.assertEqual(envio.productos.count(), 3)
        # Verificamos que al menos uno de los productos tenga la categoría anime
        for prod in envio.productos.all():
            self.assertTrue(prod.categoria.filter(id=self.cat_anime.id).exists())

    def test_generar_caja_con_relleno_forzoso(self):
        # 1 producto de Anime
        p1 = Producto.objects.create(nombre="Manga Solo", valor=Decimal('5.00'))
        p1.categoria.add(self.cat_anime)
        
        # 5 productos de Cocina (Relleno)
        for i in range(5):
            p_relleno = Producto.objects.create(nombre=f"Cuchara {i}", valor=Decimal('2.00'))
            p_relleno.categoria.add(self.cat_relleno)

        envio = Envio.objects.create(suscripcion=self.suscripcion, estado='P')
        generar_caja(envio)

        self.assertEqual(envio.productos.count(), 3)
        nombres = [p.nombre for p in envio.productos.all()] # 'nombre' según tu modelo
        self.assertIn("Manga Solo", nombres)

    def test_filtro_de_presupuesto(self):
        # Producto Caro ($100)
        p_caro = Producto.objects.create(nombre="Estatua Oro", valor=Decimal('100.00'))
        p_caro.categoria.add(self.cat_anime)
        
        # Productos Baratos ($5)
        for i in range(3):
            p_barato = Producto.objects.create(nombre=f"Llavero {i}", valor=Decimal('5.00'))
            p_barato.categoria.add(self.cat_anime)

        envio = Envio.objects.create(suscripcion=self.suscripcion, estado='P')
        generar_caja(envio)
        
        self.assertEqual(envio.productos.count(), 3)
        nombres = [p.nombre for p in envio.productos.all()]
        self.assertNotIn("Estatua Oro", nombres)