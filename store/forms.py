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
        fields = ['nombre', 'monthly_price', 'allowed_categories', 'estado', 'descripcion']
        
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
            'estado': forms.RadioSelect()

        }
        
        labels = { #los labels pe
            'nombre': 'Nombre de la Caja',
            'monthly_pricce': 'Precio mensual($)',
            'allowed_categories': 'Categorias incluidas',
            'estado': 'Estado',
            'descripcion': 'Descripción',
        }



class EnvioDespachoForm(forms.ModelForm):
    class Meta:
        model = Envio
        fields = ['numero_guia', 'estado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            estado_actual = self.instance.estado
            
            if estado_actual == 'P':
                # CAMBIO: Agregamos una etiqueta clara para que el usuario sepa que no puede guardar en 'P'
                self.fields['estado'].choices = [
                    ('P', '--- Preparando ---'),
                    ('E', 'Enviado (Listo para despachar)')
                ]
                self.fields['numero_guia'].required = False

            elif estado_actual == 'E':
                self.fields['estado'].choices = [
                    ('E', 'Enviado'),
                    ('R', 'Recibido')
                ]
                self.fields['numero_guia'].required = True

    def clean_estado(self):
        nuevo_estado = self.cleaned_data.get('estado')
        estado_actual = self.instance.estado
        if estado_actual == 'P' and nuevo_estado == 'R':
            raise forms.ValidationError("No puedes saltar de 'Preparando' a 'Recibido'.")
        return nuevo_estado

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get('estado')
        guia = cleaned_data.get('numero_guia')
        

        if self.instance.productos.count() == 0:
            raise forms.ValidationError("ERROR: Esta caja está vacía. Debes llenarla antes de intentar enviarla.")


        if estado == 'P':
            raise forms.ValidationError(
                "¡ATENCIÓN! Si aún estás preparando la caja, no puedes darle a 'Confirmar'. "
                "Para salir sin guardar cambios, utiliza el botón 'Cancelar'. "
                "Para despachar, cambia el estado a 'Enviado'."
            )
        

        if estado == 'E' and not guia:
            self.add_error('numero_guia', 'No puedes marcar como "Enviado" sin ingresar un número de guía.')

        return cleaned_data