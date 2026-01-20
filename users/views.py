from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm #importante
from django.contrib.auth import login #el login que usamos para crear usuarios

# Create your views here.
def registro(request):
    if request.method == 'POST':#si es que el metodo es post, osea intenta enviar el formulario        
        form = UserCreationForm(request.POST) #importamos para esto, #Crea un objeto formulario (form) usando el molde de registro, 
        #y rellénalo con los datos que escribió Juan (request.POST)
        if form.is_valid(): #¿Están bien los datos o Juan escribió tonterías?, que no sea repetido el usuario, que sean igual las contrase;as y asi
            usuario = form.save() #agarra los datos del formulario, conviértelos en una fila de SQL y guárdalos 
            #en la base de datos permanentemente. Y devuélveme al usuario creado en la variable usuario
            login(request, usuario)#ya que te acabas de registrar con éxito, te inicio sesión automáticamente ahora mismo para que entres directo

    else:
        form = UserCreationForm() #parentesis? para instanciarlo
    return render(request, 'users/templates/registration/registro.html', {'form':form}) #mandamos como parametro el formulario, como es eso de mandar

