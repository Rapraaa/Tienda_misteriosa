from django.db import models

# Create your models here.
class producto(models.Model):#TODO Explicar para que es el models.Model
    nombre = models.fields.CharField(max_length=50)
    categoria = models.ForeignKey(categoria, related_name="productos", on_delete=models.PROTECT )
    
    def __str__(self):
        return producto.nombre

class categoria(models.Model):
    nombre = models.fields.CharField(max_length=50)
    descripcion = models.fields.CharField(max_length=150, blank=True, null=True)

class mystery_box:
    pass

class suscripcion: 
    pass

class envios:
    pass

