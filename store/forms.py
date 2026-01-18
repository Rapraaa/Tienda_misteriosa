#para al usar mixinxs usar formularios personalizadoss
from django import forms
from .models import *

class ProductoForm(forms.ModelForm): #aca definimos un form
    class Meta:#debemos meter en meta
        model = Producto #como si fuera un mixin normal
        fields = ['nombre', 'valor', 'stock', 'categoria']
        
        # AQUÍ OCURRE LA MAGIA
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'cyber-input', 'placeholder': 'Ej: Caja Misteriosa Anime'}), #texto
            'stock': forms.NumberInput(attrs={'class': 'cyber-input', 'min': '0'}),
            'valor': forms.NumberInput(attrs={'class': 'cyber-input', 'min': '0'}),#numeros
            'categoria': forms.CheckboxSelectMultiple(), # <--- Esto convierte el select en checkboxes
            #ya que por defecto el selector es con control y es incomodo, esto es emjor, hay radiobutton tambien y muchos mas
            #https://docs.djangoproject.com/en/6.0/ref/forms/widgets/ aca

        }
        
        labels = { #los labels pe
            'nombre': 'Nombre del Producto',
            'valor': 'Precio($)',
            'stock': 'Productos Disponibles',
            'categoria': 'Categorías',
        }
    #ahora en el views hay que decir que use este form en vez de el por defecto

class CajaForm(forms.ModelForm): #aca definimos un form #TODO que haya un tipo stock de cajas pero que revise si hay el producto suficiente para armar una caja
    class Meta:
        model = Mystery_Box
        fields = ['nombre', 'monthly_price', 'allowed_categories', 'descripcion']
        
        # AQUÍ OCURRE LA MAGIA
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'cyber-input', 'placeholder': 'Ej: Caja Misteriosa Anime'}), #texto
            #! LOS ATTRS es para que envie con esos atributos al html, y con los dise;os que ya definimos sepa como adaptarlos
            #! podemos ponerlos aca para mas facilidad, o en el html, da igual a la final pero aca es mas legible
            'monthly_price': forms.NumberInput(attrs={'class': 'cyber-input', 'min': '0'}),
            'allowed_categories': forms.CheckboxSelectMultiple(attrs={'class': 'cyber-input'}),#numeros
            'descripcion': forms.TextInput(attrs={'class': 'cyber-input'}), # <--- Esto convierte el select en checkboxes
            #ya que por defecto el selector es con control y es incomodo, esto es emjor, hay radiobutton tambien y muchos mas
            #https://docs.djangoproject.com/en/6.0/ref/forms/widgets/ aca

        }
        
        labels = { #los labels pe
            'nombre': 'Nombre de la Caja',
            'monthly_pricce': 'Precio mensual($)',
            'allowed_categories': 'Categorias incluidas',
            'descripcion': 'Descripción',
        }