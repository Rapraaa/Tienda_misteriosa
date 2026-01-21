from django.db import models
from datetime import timedelta, datetime
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal

# Create your models here.
class Producto(models.Model):#TODO Explicar para que es el models.Model
    nombre = models.CharField(max_length=50)
    categoria = models.ManyToManyField('categoria', related_name="productos") #cambiamos a many2many para que peuda tener varias categorias
    #el related name es la forma en que se apoda la forma en que llamaremos desde el padre, es decir categoria
    #productos, es decir los hijos
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=1)#no acepta negativos
    
    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    #producto = models.ManyToManyField('producto')
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Mystery_Box(models.Model):
    nombre = models.CharField(max_length=50)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    allowed_categories = models.ManyToManyField('categoria', related_name="boxes")
    descripcion = models.CharField(max_length=250, blank=True, null=True)
    #DIFERENCIA DECIMALFIELD Y FLOATFIELT ES , el decimal siempre se debe usar para dinero, ya que floatfield no SIEMPRE es exacto
    #aveces 10.00 en decimal es 10.00000000001.
    estado = models.CharField(max_length=20, choices=(
        ('A', 'Activa'),
        ('I', 'Inactivo')
    ),default='A')
    OPCIONES_DESCUENTO = [
        (0, 'Sin Descuento'),
        (5, 'Descuento Basico (5%)'),
        (10, 'Descuento Estandar (10%)'),
        (15, 'Gran descuento(15%)'),
        (20, 'Super descuento (20%)'),
    ]
    porcentaje_descuento = models.IntegerField(choices=OPCIONES_DESCUENTO, default=10)
    es_exclusiva = models.BooleanField(default=False) #esclusiva de suscriptores
    @property
    def precio_suscripcion(self): #! precio para suscriptores
        if self.porcentaje_descuento == 0:
            return self.precio_base
        
        descuento = self.precio_base * (Decimal(self.porcentaje_descuento) / Decimal(100))
        return (self.precio_base - descuento).quantize(Decimal('0.01'))

    def __str__(self):
        return f"Caja {self.nombre} (${self.precio_base})"

class Suscripcion(models.Model): 
    usuario = models.OneToOneField(User, related_name='membresia', on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=(
        ('I', 'Inactiva'),
        ('A', 'Activa'),
        ('C', 'Cancelada'),
        ('P', 'Pago_pendiente')
    ), default='I')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_proximo_pago = models.DateField(null=True, blank=True)
    #TODO crear fecha de inicio
    def __str__(self):
        return f"Membresía de {self.usuario.username} - {self.estado}"
class Envio(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mis_envios')
    caja = models.ForeignKey('Mystery_Box', on_delete=models.PROTECT)
    #! LOGISTICA DE ENVIO
    fecha_envio = models.DateTimeField(default = timezone.now) #investigar auto_now_add=True
    direccion_envio = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=50, blank=True, null=True)
    codigo_postal = models.CharField(max_length=20, blank=True, null=True)
    nombre_receptor = models.CharField(max_length=100, blank=True, null=True)

    #!#################################
    productos = models.ManyToManyField('producto', related_name='envios')
    estado = models.CharField(choices=[
        ('P', 'Preparando caja'),
        ('E', 'Enviado'),
        ('R', 'Recibido')
    ], default='P')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0) #TODO esto no lo debe ver el usuario
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True) # ID de sesión de Stripe para referencia
    codigo_rastreo_interno = models.CharField(max_length=50, blank=True, null=True) #ointerno
    numero_guia = models.CharField(max_length=50, blank=True, null=True)#servientrega o fedex

#todo que valga el boton de cancelar y todos los botones
#todo CONCENTRARNOS AHORITA EN NO AGREGAR NADA NUEVO, SOLO ARREGLAR Y QUE TODO SIRVA BIEN DE LO QUE YA TENEMOS
#todo no deberia poder yo cambiar a estado recibido antes de enviar, y el recibido deberia cambiarse automaticamente con el fake traker
#// todo poder desactivar cajas