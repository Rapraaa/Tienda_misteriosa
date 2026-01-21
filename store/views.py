from django.shortcuts import render, get_object_or_404
from .models import Mystery_Box
from django.contrib.auth.decorators import login_required, permission_required
from .models import *
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .forms import ProductoForm, CajaForm, EnvioDespachoForm, CuponForm
import stripe #! para la api de stripe
from django.conf import settings #! para las llaves del stripe
from django.shortcuts import redirect #para redigirir a la api
from .utils import generar_caja, generar_id_interno, es_usuario_premium
from django.shortcuts import render
from .cart import Cart  # Importar la clase Cart
from django.http import JsonResponse  # Para respuestas AJAX
from django.contrib import messages  # Para mensajes de validación
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


class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'store/templates/CategoriaListView.html'
    context_object_name = 'categorias'

    def get_queryset(self):
        # Mostrar todas para poder reactivar/desactivar sin borrar
        return Categoria.objects.all().order_by('-activa', 'nombre')


class CategoriaCreateView(LoginRequiredMixin, CreateView, PermissionRequiredMixin):
    model = Categoria
    fields = ['nombre', 'descripcion']
    template_name = 'store/templates/CategoriaCreateUpdateView.html'
    success_url = reverse_lazy('categorias')


class CategoriaUpdateView(LoginRequiredMixin, UpdateView, PermissionRequiredMixin):
    model = Categoria
    fields = ['nombre', 'descripcion']
    template_name = 'store/templates/CategoriaCreateUpdateView.html'
    success_url = reverse_lazy('categorias')


@login_required
@permission_required('store.change_categoria', raise_exception=True)
def categoria_toggle_activa(request, pk):
    # No se borra: se desactiva/activa para no romper relaciones ManyToMany existentes
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.activa = not categoria.activa
        categoria.save(update_fields=['activa'])
    return redirect('categorias')


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
def crear_checkout_session(request, id): #! EStE STRIPE ES PARA COMPRAS NORMALES
    caja = get_object_or_404(Mystery_Box, id=id,)  #vemos que caja quiere comprar
    dominio = 'http://localhost:8000' #este dominio luego le damos a stripe, para que sepa a donde volver luego, es como el url base
    #! DOCUMENTACION STRIPE API https://docs.stripe.com/api/checkout/sessions/create

    es_premium = es_usuario_premium(request.user) #vemos si es premiun el usuario

    if caja.es_exclusiva and not es_premium:
        return redirect('pagina_hazte_premium') # Mandarlo a que se suscriba si la caja es premium

    if caja.estado != 'A': #validar que sea activa, sino con el link nos hacen la 13 14
            # TODO Opcional: Mandar un mensaje de error con 'messages' de Django o alguna vista personalizada bien linda bacana sexy sensuala
            return redirect('home')
    if es_premium: #true or false
        precio_final = caja.precio_suscripcion # El precio con descuento
    else:
        precio_final = caja.precio_base # Precio normal

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
                        'unit_amount': int(precio_final * 100), # Stripe usa centavos (25.00 -> 2500)
                        'product_data': { #datos del producto
                            'name': f"Compra de {caja.nombre}", #el nombre
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
    
    # Primero intentamos buscar si ya existe un envío con este session_id
    envio_existente = Envio.objects.filter(stripe_session_id=session_id, usuario=request.user).first()
    
    if envio_existente:
        # Si ya existe, solo mostramos la info sin crear nada nuevo
        return render(request, "store/templates/pago_exitoso.html", {
            'caja': envio_existente.caja,
            'envio': envio_existente
        })

    # 2. PROCESO DE COMPRA REAL (solo si no existe)
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

    suscripcion, _ = Suscripcion.objects.get_or_create(usuario=request.user)
    nuevo_envio = Envio.objects.create(
        usuario=request.user,
        caja=caja,
        stripe_session_id=session_id,  # Guardamos el session_id de Stripe
        nombre_receptor=datos_envio.get('name') or request.user.username,
        direccion_envio=f"{info_direccion.get('line1', '')} {info_direccion.get('line2', '')}".strip(),
        ciudad=info_direccion.get('city', ''),
        pais=info_direccion.get('country', ''),
        codigo_postal=info_direccion.get('postal_code', ''),
        # AQUÍ: Tu código bonito que tanto querías
        codigo_rastreo_interno=generar_id_interno(),
        # El número de guía queda VACÍO para el despachador
        numero_guia=None, 
        estado='P'
    ) 
    generar_caja(nuevo_envio)

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
        # CAMBIO por la logica: Ahora select_related usa los campos directos usuario'y 'cajita
        return Envio.objects.filter(estado='P').select_related('usuario', 'caja').order_by('fecha_envio')
    

class EnviosUpdateView(UpdateView):
    model = Envio
    form_class = EnvioDespachoForm
    template_name = 'store/templates/EnviosUpdateView.html'
    success_url = reverse_lazy('envios')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        envio = self.object  
        comprador = envio.usuario # el cliente que hizo la compra
        

        context['items_a_empacar'] = envio.productos.all()
        

        if hasattr(comprador, 'membresia') and comprador.membresia.estado == 'A':
            precio_pagado = envio.caja.precio_suscripcion
        else:
            precio_pagado = envio.caja.precio_base
            

        costo_real = envio.valor_total
        margen = precio_pagado - costo_real
        
        context['finanzas'] = {
            'pagado': precio_pagado,
            'costo': costo_real,
            'margen': margen,
            'es_rentable': margen > 0
        }
        
        return context
    
    def form_valid(self, form):
        """Validar que se hayan seleccionado productos antes de confirmar envío"""
        envio = form.instance
        
        # Si está intentando marcar como "Enviado" pero no tiene productos
        if envio.estado == 'E' and envio.productos.count() == 0:
            messages.error(
                self.request, 
                '❌ Debe seleccionar al menos un producto antes de confirmar el envío'
            )
            return self.form_invalid(form)
        
        messages.success(self.request, '✅ Envío actualizado correctamente')
        return super().form_valid(form)
    
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
            envio = Envio.objects.select_related('usuario', 'caja').get(codigo_rastreo_interno=guia)
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
    # ANTES: Envio.objects.filter(suscripcion__usuario=request.user).select_related('suscripcion__caja')
    # AHORA: Usamos los campos directos que pusimos en el modelo Envio
    mis_envios = Envio.objects.filter(
        usuario=request.user
    ).select_related('caja').order_by('-id')
    
    return render(request, 'store/templates/profile.html', {
        'mis_envios': mis_envios
    })
#todo si se llama domenica puede usar el cupon de kamasutra

#todo, hacer carrito de compras, y que se pueda agregar cosas al carrito de compras sin iniciar sesion pero que ya de ahi para pagar pida iniciar sesion y se pasen las cosas


#!STRIPE PARA SUSCRIPCIONES

#* variable para el precio de la membresia
PRECIO_MEMBRESIA_USD = 9.99

@login_required
def crear_suscripcion_premium(request):
    dominio = "http://localhost:8000"
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(PRECIO_MEMBRESIA_USD * 100),
                    'product_data': {
                        'name': 'Mysterio Pass - Membresía Premium',
                        'description': 'Acceso a descuentos exclusivos y cajas VIP en toda la tienda.',
                    },
                },
                'quantity': 1,
            }],
            mode='payment', # Usamos payment para cobro único que activa 30 días
            success_url=f'{dominio}/membresia-exitosa/?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{dominio}/perfil/',
        )
        return redirect(checkout_session.url)
    except Exception as e:
        return render(request, 'store/templates/error_pago.html', {'error': str(e)})

@login_required
def membresia_exitosa(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('home')

    # si no existe la creamos
    suscripcion, created = Suscripcion.objects.get_or_create(
        usuario=request.user,
        defaults={'estado': 'I'} #si es nueva inicia en inactiva, esto para el paso de mas adelante
    )

    hoy = timezone.now().date()

    # si es que ya esta activa, osea ya se se activo, y tiene fecha de proximo pago y esta es menor a hoy, osea no era hoy su fecha de pago
    if suscripcion.estado == 'A' and suscripcion.fecha_proximo_pago and suscripcion.fecha_proximo_pago > hoy:
        #Sumamos 30 días a su fecha de vencimiento actual
        nueva_fecha = suscripcion.fecha_proximo_pago + timedelta(days=30)
    else:
        # el usuaruo es nuevo o ya expiro su membresia, ahi solo le aumentamos 30 a la fecha de hoy
        nueva_fecha = hoy + timedelta(days=30)

    # actualizamos lso datos y activamos la suscripsion
    suscripcion.estado = 'A'
    suscripcion.fecha_proximo_pago = nueva_fecha
    suscripcion.save()

    return render(request, 'store/templates/membresia_confirmada.html')


#! ==================== CARRITO DE COMPRAS ====================

def agregar_al_carrito(request, id):
    """Agrega una caja al carrito (funciona con AJAX y sin AJAX)"""
    caja = get_object_or_404(Mystery_Box, id=id)
    
    # Validar que la caja esté activa
    if caja.estado != 'A':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Esta caja no está disponible'})
        return redirect('home')
    
    # Validar cajas exclusivas
    if caja.es_exclusiva and not es_usuario_premium(request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Esta caja es exclusiva para socios premium'})
        return redirect('suscribirse_premium')
    
    cart = Cart(request)
    cart.add(caja_id=id, cantidad=1)
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.get_count(),
            'message': f'{caja.nombre} agregada al carrito'
        })
    
    # Si no es AJAX, redirigir al carrito
    return redirect('ver_carrito')


def ver_carrito(request):
    """Muestra la página del carrito con cupones"""
    from decimal import Decimal
    cart = Cart(request)
    items = cart.get_items()
    total = cart.get_total()
    
    # Obtener cupón de la sesión
    cupon_codigo = request.session.get('cupon_codigo')
    cupon_descuento = Decimal(str(request.session.get('cupon_descuento', 0)))
    
    # Calcular total final
    total_final = total - cupon_descuento if cupon_descuento > 0 else total
    
    return render(request, 'store/templates/carrito.html', {
        'items': items,
        'total': total,
        'cart_count': cart.get_count(),
        'cupon_codigo': cupon_codigo,
        'cupon_descuento': cupon_descuento,
        'total_final': total_final
    })


def eliminar_del_carrito(request, id):
    """Elimina un item del carrito"""
    cart = Cart(request)
    cart.remove(caja_id=id)
    
    # Si es AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.get_count(),
            'total': float(cart.get_total())
        })
    
    return redirect('ver_carrito')


@login_required
def checkout_carrito(request):
    """Crea una sesión de Stripe para el carrito completo"""
    cart = Cart(request)
    items = cart.get_items()
    
    if not items:
        return redirect('ver_carrito')
    
    dominio = 'http://localhost:8000'
    es_premium = es_usuario_premium(request.user)
    
    # Validar cajas exclusivas
    for item in items:
        if item['caja'].es_exclusiva and not es_premium:
            return redirect('suscribirse_premium')
    
    # Crear line_items para Stripe
    line_items = []
    for item in items:
        caja = item['caja']
        cantidad = item['cantidad']
        
        # Determinar precio
        if es_premium:
            precio_final = caja.precio_suscripcion
        else:
            precio_final = caja.precio_base
        
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(precio_final * 100),  # Stripe usa centavos
                'product_data': {
                    'name': f"{caja.nombre}",
                    'description': caja.descripcion or "Caja misteriosa",
                },
            },
            'quantity': cantidad,
        })
    
    # Verificar si hay cupón en la sesión
    cupon_descuento = request.session.get('cupon_descuento', 0)
    cupon_codigo = request.session.get('cupon_codigo')
    discounts = []
    
    if cupon_descuento > 0 and cupon_codigo:
        try:
            # Crear cupón en Stripe al vuelo
            cupon_stripe = stripe.Coupon.create(
                amount_off=int(float(cupon_descuento) * 100),
                currency='usd',
                duration='once',
                name=f"Cupón {cupon_codigo}"
            )
            discounts = [{'coupon': cupon_stripe.id}]
        except Exception as e:
            print(f"Error creando cupón Stripe: {e}")
            # Si falla, proceder sin descuento o manejar error (opcional)

    try:
        # Crear sesión de checkout en Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            shipping_address_collection={'allowed_countries': ['EC', 'US']},
            line_items=line_items,
            mode='payment',
            discounts=discounts,  # Aplicar descuento
            success_url=f'{dominio}/carrito/compra-exitosa/?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{dominio}/carrito/',
        )
        
        return redirect(checkout_session.url)
        
    except Exception as e:
        return render(request, 'store/templates/error_pago.html', {'error': str(e)})


@login_required
def compra_exitosa_carrito(request):
    """Procesa la compra exitosa del carrito"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('home')
    
    # Verificar si ya procesamos este pago
    envios_existentes = Envio.objects.filter(stripe_session_id=session_id, usuario=request.user)
    if envios_existentes.exists():
        # Ya se procesó, mostrar los envíos
        return render(request, "store/templates/pago_exitoso_carrito.html", {
            'envios': envios_existentes
        })
    
    # Obtener items del carrito
    cart = Cart(request)
    items = cart.get_items()
    
    if not items:
        return redirect('home')
    
    # Obtener datos de envío de Stripe
    try:
        session_stripe = stripe.checkout.Session.retrieve(session_id)
        datos_envio = session_stripe.get('shipping_details') or session_stripe.get('customer_details')
        nombre_cliente = datos_envio.get('name') or request.user.username
        info_direccion = datos_envio.get('address')
    except Exception as e:
        return render(request, 'store/templates/error_pago.html', {'error': f"Error de Stripe: {str(e)}"})
    
    # Crear suscripción si no existe
    suscripcion, _ = Suscripcion.objects.get_or_create(usuario=request.user)
    
    # CAMBIO: Crear UN SOLO Envio con un código único para todo el carrito
    codigo_unico = generar_id_interno()
    
    # Crear el envío único para todo el carrito
    envio_unico = Envio.objects.create(
        usuario=request.user,
        caja=items[0]['caja'],  # Usamos la primera caja como referencia
        stripe_session_id=session_id,
        nombre_receptor=nombre_cliente,
        direccion_envio=f"{info_direccion.get('line1', '')} {info_direccion.get('line2', '')}".strip(),
        ciudad=info_direccion.get('city', ''),
        pais=info_direccion.get('country', ''),
        codigo_postal=info_direccion.get('postal_code', ''),
        codigo_rastreo_interno=codigo_unico,  # Código único para todo
        numero_guia=None,
        estado='P'
    )
    
    # Generar productos para cada caja y agregarlos al envío único
    for item in items:
        caja = item['caja']
        cantidad = item['cantidad']
        
        # Por cada caja en el carrito, generar sus productos
        for _ in range(cantidad):
            generar_caja(envio_unico)  # Esto agrega productos al envío
    
    # Vaciar el carrito
    cart.clear()
    
    return render(request, "store/templates/pago_exitoso_carrito.html", {
        'envio': envio_unico,
        'codigo_rastreo': codigo_unico,
        'total_cajas': sum(item['cantidad'] for item in items)
    })


# Append to views.py

#! ==================== SISTEMA DE CUPONES ====================

def validar_cupon(request):
    """Valida un cupón y lo guarda en la sesión"""
    if request.method == 'POST':
        codigo_cupon = request.POST.get('codigo', '').strip().upper()
        if not codigo_cupon:
            messages.error(request, 'Ingresa un código de cupón')
            return redirect('ver_carrito')
        try:
            from .models import Cupon
            cupon = Cupon.objects.get(codigo=codigo_cupon)
        except Cupon.DoesNotExist:
            messages.error(request, f'El cupón "{codigo_cupon}" no es válido')
            return redirect('ver_carrito')
        cart = Cart(request)
        total = cart.get_total()
        es_valido, mensaje = cupon.es_valido(request.user if request.user.is_authenticated else None, total)
        if not es_valido:
            messages.error(request, mensaje)
            return redirect('ver_carrito')
        descuento = cupon.calcular_descuento(total)
        request.session['cupon_codigo'] = codigo_cupon
        request.session['cupon_descuento'] = float(descuento)
        messages.success(request, f'✅ Cupón {codigo_cupon} aplicado: ${descuento} de descuento')
        return redirect('ver_carrito')
    return redirect('ver_carrito')

def remover_cupon(request):
    """Remueve el cupón de la sesión"""
    if 'cupon_codigo' in request.session:
        del request.session['cupon_codigo']
    if 'cupon_descuento' in request.session:
        del request.session['cupon_descuento']
    messages.info(request, 'Cupón removido')
    return redirect('ver_carrito')
# CRUD de Cupones - Agregar al final de views.py

class CuponListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cupon
    template_name = 'store/templates/cupones/lista.html'
    context_object_name = 'cupones'
    permission_required = 'store.view_cupon'
    paginate_by = 20
    
    def get_queryset(self):
        return Cupon.objects.all().order_by('-fecha_inicio')


class CuponCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Cupon
    form_class = CuponForm
    template_name = 'store/templates/cupones/form.html'
    permission_required = 'store.add_cupon'
    success_url = reverse_lazy('cupones_lista')
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Cupón {form.instance.codigo} creado exitosamente')
        return super().form_valid(form)


class CuponUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Cupon
    form_class = CuponForm
    template_name = 'store/templates/cupones/form.html'
    permission_required = 'store.change_cupon'
    success_url = reverse_lazy('cupones_lista')
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Cupón {form.instance.codigo} actualizado')
        return super().form_valid(form)


class CuponDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Cupon
    template_name = 'store/templates/cupones/confirmar_eliminar.html'
    permission_required = 'store.delete_cupon'
    success_url = reverse_lazy('cupones_lista')
    
    def delete(self, request, *args, **kwargs):
        cupon = self.get_object()
        messages.success(request, f'🗑️ Cupón {cupon.codigo} eliminado')
        return super().delete(request, *args, **kwargs)


class CuponDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Cupon
    template_name = 'store/templates/cupones/detalle.html'
    permission_required = 'store.view_cupon'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener historial de cambios
        context['historial'] = self.object.history.all()[:20]
        return context


# Vista de Logs de Auditoría
class AuditLogView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Vista para mostrar logs de auditoría de todos los modelos"""
    template_name = 'store/templates/admin/audit_log.html'
    permission_required = 'store.view_cupon'
    paginate_by = 50
    context_object_name = 'logs'
    
    def get_queryset(self):
        from django.contrib.contenttypes.models import ContentType
        
        # Obtener historial de todos los modelos
        logs = []
        
        # Cupones
        from .models import Cupon
        if hasattr(Cupon, 'history'):
            for record in Cupon.history.all()[:50]:
                logs.append({
                    'model': 'Cupón',
                    'object': record.codigo,
                    'action': self.get_action_display(record.history_type),
                    'user': record.history_user,
                    'date': record.history_date,
                    'changes': self.get_changes(record)
                })
        
        # Envios
        from .models import Envio
        if hasattr(Envio, 'history'):
            for record in Envio.history.all()[:50]:
                logs.append({
                    'model': 'Envío',
                    'object': record.codigo_rastreo_interno or f'Envío #{record.id}',
                    'action': self.get_action_display(record.history_type),
                    'user': record.history_user,
                    'date': record.history_date,
                    'changes': self.get_changes(record)
                })
        
        # Ordenar por fecha
        logs.sort(key=lambda x: x['date'], reverse=True)
        return logs[:self.paginate_by]
    
    def get_action_display(self, history_type):
        actions = {
            '+': 'Creado',
            '~': 'Modificado',
            '-': 'Eliminado'
        }
        return actions.get(history_type, 'Desconocido')
    
    def get_changes(self, record):
        """Obtiene los cambios realizados"""
        if record.history_type == '+':
            return 'Registro creado'
        elif record.history_type == '-':
            return 'Registro eliminado'
        else:
            return 'Registro modificado'
