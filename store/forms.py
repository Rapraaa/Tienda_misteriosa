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


from django import forms
from .models import Envio

class EnvioDespachoForm(forms.ModelForm):
    class Meta:
        model = Envio
        fields = ['numero_guia', 'estado']
        widgets = {
            'numero_guia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: FEDEX-123456'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get('estado')
        guia = cleaned_data.get('numero_guia')
        
        # self.instance se refiere al objeto Envio que estamos editando
        if self.instance.productos.count() == 0:
            raise forms.ValidationError("ERROR: Esta caja está vacía. Ejecuta lllena la caja antes de enviar.")

        # Si pone guía, TIENE que poner Enviado. Si pone Enviado, TIENE que poner guía.
        if guia and estado == 'P':
            self.add_error('estado', 'ADVERTENCIA: Tienes un número de guía, debes cambiar el estado a "Enviado" para continuar.')
        
        if estado == 'E' and not guia:
            self.add_error('numero_guia', 'ADVERTENCIA: No puedes marcar como "Enviado" sin un número de guía.')

        return cleaned_data