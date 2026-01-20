from django.shortcuts import render, get_object_or_404
from .models import Mystery_Box
from django.contrib.auth.decorators import login_required, permission_required
from .models import *
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .forms import ProductoForm, CajaForm, EnvioDespachoForm #imprtamos el form que hicimos
import stripe #! para la api de stripe
from django.conf import settings #! para las llaves del stripe
from django.shortcuts import redirect #para redigirir a la api
from .utils import generar_caja, generar_id_interno
from django.shortcuts import render
# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY #! mi api

def home(request):
    cajitas= Mystery_Box.objects.all()
    return render(request, "store/templates/home.html", {'boxes' : cajitas}) 
    #funcion render


def box(request, id): #COMO LAS CAJAS RECIBEN UN ID PARA VER QUE HACER CON EL HTML PONEMOS ACA EL ID
    box = get_object_or_404(Mystery_Box, id=id)
    return render(request, "store/templates/detalle_caja.html", {'caja' : box})
    
class CajaCreateView(LoginRequiredMixin, CreateView, PermissionRequiredMixin): #TODO al crear que mande a un mensaje de exito

    model = Mystery_Box
    form_class = CajaForm
    template_name = 'store/templates/CajaUpdateCreateView.html'
    success_url = reverse_lazy('home')


class CajaUpdateView(LoginRequiredMixin, UpdateView, PermissionRequiredMixin): 
    model = Mystery_Box
    form_class = CajaForm
    template_name = 'store/templates/CajaUpdateCreateView.html'
    success_url = reverse_lazy('home')

#!TODO  Poder activar y desactivar una caja



class ProductoListView(LoginRequiredMixin, ListView): 
    queryset = Producto.objects.prefetch_related('categoria') #prefetch related es para many to many
    template_name = 'store/templates/ProductoListView.html'
    context_object_name = 'productos'
    #TODO paginacion paginate_by = 10

class ProductoCreateView(LoginRequiredMixin, CreateView, PermissionRequiredMixin):
    model = Producto
    form_class = ProductoForm
    template_name = 'store/templates/ProductoCreateView.html'
    success_url = reverse_lazy('productos')
    #Todo permission_required = 1231

class ProductoUpdateView(LoginRequiredMixin, UpdateView, PermissionRequiredMixin):
    model = Producto #todo revisar que pasa si a un producto que ya esta en una categoria, en una caja, comprado le cambio su
    #categoria
    form_class = ProductoForm
    template_name = 'store/templates/ProductoUpdateView.html'
    success_url = reverse_lazy('productos')
    #Todo permission_required = 1231


class SuscripcionListView(LoginRequiredMixin, ListView): #todo esto ed envios global, queremos que cada usuario pueda ver su propio historial
    model = Suscripcion
    template_name = 'store/templates/SuscripcionListView.html'
    context_object_name = 'suscripciones'
    
    def get_queryset(self): #probar este luego
        usuario_actual = self.request.user
        if usuario_actual.has_perm('store.view_suscripcion'): #TODO en los modelos crear permisos personalizados para lo que ocupemos
            return Suscripcion.objects.all().order_by('-id')
        else:
            return Suscripcion.objects.filter(usuario=self.request.user).order_by('-id')
    #sobreescribimos el metodo original que el orginal trae todos, ese solo trae el del usuario
    #? self.request tiene toda la informacion de la peticion actual (ip, cookies, usuario, etc) el user es el que paso el login requured
    #el -id es para que se ordene de forma descendente, y se vea las mas nuevas primero

#TODO direccion de envio y de contacto de el usuario
#TODO logistica de envios, que los administradores vean los pendientes, los armen, los envien y den el codigo de envio

#api 
#*  IMPORTANTE ACA DECIRLE CUAL ES LA KEY, LA SECRETA, SIN ESTO DARA ERROR
def crear_checkout_session(request, id):
    caja = get_object_or_404(Mystery_Box, id=id) #vemos que caja quiere comprar
    dominio = 'http://localhost:8000' #este dominio luego le damos a stripe, para que sepa a donde volver luego, es como el url base
    #! DOCUMENTACION STRIPE API https://docs.stripe.com/api/checkout/sessions/create

    if caja.estado != 'A': #validar que sea activa, sino con el link nos hacen la 13 14
            # TODO Opcional: Mandar un mensaje de error con 'messages' de Django o alguna vista personalizada bien linda bacana sexy sensuala
            return redirect('home')
    suscripcion_existente = Suscripcion.objects.filter( #revisamos que no se pueda suscribir de neuvo a algo que ya esta
        usuario=request.user,
        caja=caja,
        estado='A' # Solo nos importa si está activa
    ).exists()


    if suscripcion_existente:
            return redirect('home') # TODO: Redirigir a una página que diga que ya tiene esa suscripcion o caka
    try:
        # Creamos la sesión de pago en Stripe, es la sesion temporal donde pone sus datos y tal y se decide si pasa(pagA) o no
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'], #tipo de pago, hay mas como cripto por ejemplo
            #! VAmos a pedir la direccion de envio tambien
            shipping_address_collection={'allowed_countries':['EC', 'US'],
                                         },
            line_items=[ #el carrito de compras
                {
                    # Definimos el producto
                    'price_data': { #esto son los datos de los precios
                        'currency': 'usd', #dolares
                        'unit_amount': int(caja.monthly_price * 100), # Stripe usa centavos (25.00 -> 2500)
                        'product_data': { #datos del producto
                            'name': f"Suscripción: {caja.nombre}", #el nombre
                            'description': caja.descripcion, #descripcionn
                        },
                    },
                    'quantity': 1, #cantidad
                },
            ],
            mode='payment', # Usamos 'payment' para simplificar (cobro único inicial), #!hay el mensual pero toca configurar mucha vaina en el stripe
                # si paga bien, Stripe lo manda a esta URL que es la vista de exito
            success_url=f'{dominio}/compra-exitosa/{caja.id}/?session_id={{CHECKOUT_SESSION_ID}}',
                
                # si se arrepiente y cancela, vuelve al detalle de la caja
            cancel_url=f'{dominio}/caja/{caja.id}/',
        )
            
            # Redirigimos al usuario a la URL que Stripe nos dio
        return redirect(checkout_session.url)
            
    except Exception as e:
        return render(request, 'store/templates/error_pago.html', {'error': str(e)}) 



@login_required
def compra_exitosa(request, id):
    # Validamos que venga de Stripe por temas de seguridad
    session_id = request.GET.get('session_id')
    if not session_id:
         #si no viene de stipe directo pal home
        return redirect('home')
    #obtenemos el objeto
    caja = get_object_or_404(Mystery_Box, id=id)
    
    #! PEDIMOS LAS DIRECCIONES QUE PUSO EL SAPO DEL USUARIO
    try:
        session_stripe = stripe.checkout.Session.retrieve(session_id) #la sesion, para que sepa cua lde todas coger. le pedimos los datos de esa id
        datos_envio = session_stripe.get('shipping_details') or session_stripe.get('customer_details') #guardamos direccion
        nombre_cliente = datos_envio.get('name') or request.user.username #guardamos nombre
        #print(f"{datos_envio}, {session_stripe}. {nombre_cliente}")
        info_direccion = datos_envio.get('address')

    except Exception as e:
        #si es que falla
        return render(request, 'store/templates/error_pago.html', {'error': f"Error de Stripe: {str(e)}"}) #mandamos a la pagina de error
    #! LÓGICA DE NEGOCIO: CREAR SUSCRIPCIÓN Y PRIMER ENVÍO
    #?Usamos get_or_create para que si recarga la página no se cobre doble
    suscripcion, created = Suscripcion.objects.get_or_create( #si hay suscripcion pq recargo pagina no pasa nada, 
        #sino la crea, esto pq tuvimos un fallo que si recargabamos se repetia la suscripcion 
        usuario=request.user, 
        caja=caja,
        estado='A', #activo
        defaults={'fecha_proximo_pago': timezone.now() + timedelta(days=30), #1 mes pal proximo pago\
        }

    )

    if created: #si es que es nueva la suscripcion, osea no se actualizo la pagina
        #generamos el primer envio
        codigo = generar_id_interno() #el codigo
        nuevo_envio = Envio.objects.create(
            suscripcion=suscripcion,
            estado='P',
            nombre_receptor = nombre_cliente,
            
            # Usamos 'info_direccion' que preparamos arriba
            direccion_envio = f"{info_direccion.get('line1', '')} {info_direccion.get('line2', '')}".strip(),
            ciudad = info_direccion.get('city', ''),
            pais = info_direccion.get('country', ''),
            codigo_postal = info_direccion.get('postal_code', ''),
            codigo_rastreo_interno = codigo
   
        )
        generar_caja(nuevo_envio)
        #TODO aca toca llamar al algoritmo que aun no ahcemos en modelos de los productos random
    else:
        # Si recargó la página, buscamos el ulitmo envio de suscripcoon
        nuevo_envio = Envio.objects.filter(suscripcion=suscripcion).last()

    # CAMBIO IMPORTANTE: Pasamos 'envio' al contexto, no solo 'caja'
    return render(request, "store/templates/pago_exitoso.html", {
            'caja': caja,
            'envio': nuevo_envio 
        })

#todo al estar por acabar un boton para renovar suscripcion
#todo para que tenga un poco mas de sentido que mande varias cajas de la misma por semana, pero que pague el mes, y que estas tengan un mini descuento
#todo que tambien se pueda comprar solo una caja, un poco mas caro que la suscripcion
#todo que la id de transaccion al completar el pago sea real xd
#todo IMPORTANTE que no deje suscribirse a una caja ya suscrita, pq intente y me cobro 2 veces xd, obvio solo se hace 1 suscripcion
#todo mejorar el detalle de la caja
#todo la logistica de envios, que vea las cajas sin enviar pendientes, formulario para poner numero de guia, y cambiar el estado
#todo las funciones para calcular las coas en models
#todo algoritmo de suerte
#todo crear una pagina para simular el rastreo del pedido (fake tracker)
#TODO PORDER CREAR CATEGORIAS DESDE LA PARTE DE CREAR PRODUCTO

#todo api para los productos


class EnviosListView(ListView):
    model = Envio
    template_name = 'store/templates/EnviosListView.html'
    context_object_name = 'envios'

    def get_queryset(self):
        # Filtramos solo lo que está en preparacion
        # Usamos select_related para traer los datos del usuario y la caja de una vez
        return Envio.objects.filter(estado='P').select_related('suscripcion__usuario', 'suscripcion__caja').order_by('fecha_envio')
    

class EnviosUpdateView(UpdateView):
    model = Envio
    form_class = EnvioDespachoForm
    template_name = 'store/templates/EnviosUpdateView.html'
    success_url = reverse_lazy('envios') # Redirige a la lista al terminar

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        envio = self.object
        
        #enviamos los productosque hay que empacar
        context['items_a_empacar'] = envio.productos.all()
        
        #calcula el margen de ganancia o perdida
        precio_pagado = envio.suscripcion.caja.monthly_price
        costo_real = envio.valor_total
        margen = precio_pagado - costo_real
        
        context['finanzas'] = {
            'pagado': precio_pagado,
            'costo': costo_real,
            'margen': margen,
            'es_rentable': margen > 0
        }
        
        return context
    
#todo validar al comprar la caja que no se puedda comprar si esta esta inactiva, ya que aunque el boton se bloquea si entro por el link pues pene
#todo IMPORTANTISIMO, que en el home los usuarios vean solo las activas, solo alguien con permisos las inactivas
#todo GRUPOS Bodeguero, meten y administran productos, (podria ser crear cajas, activar y sedasctivar pero creo que por seguridad eso deberia poder solo el gerente)
#todo GRUPOS Gerente(Subir productos nuevos, crear cajas, activar/desactivar cajas)
#todo GRUPO usuarios
#todo grpo logistica(envian y ponen cosas en la caja)
"""
Clientes: Compran y ven.

Bodegueros: Son los dueños del inventario (crean productos).

Logística: Son los que mueven las cajas (despachan y actualizan estados).

Gerente: El patrón (supervisa todo y maneja el negocio).
"""
#todo peddir direccion de envio

#todo cupones
#todo logs
#todo descuentos
#todo registrar usuarios de staffs
#todo tema de reportes, facturas y todo eso
#todo reporte de todos o de servicios
#todo cancelaciones

#TODO NO DEJAR DARLE A CONFIRMAR ENVIO SI ESTA EN PREPARANDO CAJA, SOLO CANCELAR
#todo SI AUN NO LO ENVIO NO LO PUEDE RECIBIR


def rastrear_pedido(request): 
    envio = None
    error = None
    guia = request.GET.get('guia') # Capturamos el código de la URL

    if guia:
        try:
            # Buscamos el envío por número de guía
            envio = Envio.objects.select_related('suscripcion__caja').get(codigo_rastreo_interno=guia)
        except Envio.DoesNotExist:
            error = "No encontramos ningún pedido con ese número de guía. Revisa que esté bien escrito."

    return render(request, 'store/templates/rastreo.html', {
        'envio': envio,
        'error': error,
        'guia_buscada': guia
    })


#Todo tema imopuestos, precio de envio, que si el iva cambia, los registros nuevos no pueden cambiar el iva, precio a los envios de usa

@login_required
def perfil(request):

    mis_envios = Envio.objects.filter( #filtarmos envios que la suscripcion sea el usuario actual
        suscripcion__usuario=request.user
    ).select_related('suscripcion__caja').order_by('-id') #ordenamos de mas recientes a mas viejos
    
    return render(request, 'store/templates/profile.html', {
        'mis_envios': mis_envios
    })

#todo si se llama domenica puede usar el cupon de kamasutra