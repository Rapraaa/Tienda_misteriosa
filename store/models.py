from django.db import models
from datetime import timedelta, datetime
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from simple_history.models import HistoricalRecords

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


class CarritoItem(models.Model):
    """Modelo para almacenar items del carrito de usuarios autenticados"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carrito_items')
    caja = models.ForeignKey('Mystery_Box', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario', 'caja')  # Un usuario no puede tener la misma caja duplicada en el carrito
    
    def __str__(self):
        return f"{self.usuario.username} - {self.caja.nombre} x{self.cantidad}"
    
    @property
    def subtotal(self):
        """Calcula el subtotal considerando si el usuario es premium"""
        from .utils import es_usuario_premium
        es_premium = es_usuario_premium(self.usuario)
        precio = self.caja.precio_suscripcion if es_premium else self.caja.precio_base
        return precio * self.cantidad

class Cupon(models.Model):
    """Modelo para cupones de descuento"""
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código del cupón")
    descuento_porcentaje = models.IntegerField(default=0, help_text="Descuento en porcentaje (0-100)")
    descuento_fijo = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Descuento fijo en dólares")
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateTimeField()
    fecha_expiracion = models.DateTimeField()
    usos_maximos = models.IntegerField(null=True, blank=True, help_text="Dejar vacío para usos ilimitados")
    usos_actuales = models.IntegerField(default=0)
    solo_premium = models.BooleanField(default=False, help_text="Solo para usuarios premium")
    monto_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monto mínimo de compra")
    history = HistoricalRecords()  # Historial de cambios
    
    def __str__(self):
        return f"{self.codigo} - {self.descuento_porcentaje}% / ${self.descuento_fijo}"
    
    def es_valido(self, usuario=None, monto_compra=0):
        """Valida si el cupón puede ser usado"""
        from django.utils import timezone
        from .utils import es_usuario_premium
        
        ahora = timezone.now()
        
        # Verificar si está activo
        if not self.activo:
            return False, "Este cupón no está activo"
        
        # Verificar fechas
        if ahora < self.fecha_inicio:
            return False, "Este cupón aún no es válido"
        if ahora > self.fecha_expiracion:
            return False, "Este cupón ha expirado"
        
        # Verificar usos
        if self.usos_maximos and self.usos_actuales >= self.usos_maximos:
            return False, "Este cupón ha alcanzado el límite de usos"
        
        # Verificar si es solo para premium
        if self.solo_premium and usuario:
            if not es_usuario_premium(usuario):
                return False, "Este cupón es solo para usuarios premium"
        
        # Verificar monto mínimo
        if monto_compra < self.monto_minimo:
            return False, f"El monto mínimo de compra es ${self.monto_minimo}"
        
        return True, "Cupón válido"
    
    def calcular_descuento(self, monto):
        """Calcula el descuento a aplicar"""
        if self.descuento_porcentaje > 0:
            descuento = monto * (Decimal(self.descuento_porcentaje) / Decimal(100))
        else:
            descuento = self.descuento_fijo
        
        # El descuento no puede ser mayor al monto total
        return min(descuento, monto)
    
    def usar(self):
        """Incrementa el contador de usos"""
        self.usos_actuales += 1
        self.save()

class CuponUso(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cupones_usados')
    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE, related_name='usos')
    fecha_uso = models.DateTimeField(auto_now_add=True)
    descuento_aplicado = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.usuario.username} usó {self.cupon.codigo}"

#todo que valga el boton de cancelar y todos los botones
#todo CONCENTRARNOS AHORITA EN NO AGREGAR NADA NUEVO, SOLO ARREGLAR Y QUE TODO SIRVA BIEN DE LO QUE YA TENEMOS
#todo no deberia poder yo cambiar a estado recibido antes de enviar, y el recibido deberia cambiarse automaticamente con el fake traker
#// todo poder desactivar cajas