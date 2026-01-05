from django.db import models
from datetime import timedelta, datetime
from django.utils import timezone

# Create your models here.
class Producto(models.Model):#TODO Explicar para que es el models.Model
    nombre = models.CharField(max_length=50)
    categoria = models.ManyToManyField('categoria', related_name="productos") #cambiamos a many2many para que peuda tener varias categorias
    #el related name es la forma en que se apoda la forma en que llamaremos desde el padre, es decir categoria
    #productos, es decir los hijos
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return self.nombre

class Mystery_Box(models.Model):
    nombre = models.CharField(max_length=50)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    allowed_categories = models.ManyToManyField('categoria', related_name="categoria")
    descripcion = models.CharField(max_length=250, blank=True, null=True)
    #DIFERENCIA DECIMALFIELD Y FLOATFIELT ES , el decimal siempre se debe usar para dinero, ya que floatfield no SIEMPRE es exacto
    #aveces 10.00 en decimal es 10.00000000001.
    def __str__(self):
        return f"Caja {self.nombre}"

class Suscripcion(models.Model): 
    #usuario = models.ForeignKey(users.usuarios, related_name='usuario, on_delete=models.PROTECT)
    caja = models.ForeignKey('mystery_box', related_name='caja', on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=(
        ('A', 'Activa'),
        ('C', 'Cancelada'),
        ('P', 'Pago_pendiente')
    ))
    fecha_proximo_pago = models.DateField(default = timezone.now)
class Envios(models.Model):
    suscripcion = models.ForeignKey('suscripcion', related_name='suscripcion', on_delete=models.PROTECT)
    fecha_envio = models.DateField(default = timezone.now)
    productos = models.ManyToManyField('producto', related_name='productos')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

