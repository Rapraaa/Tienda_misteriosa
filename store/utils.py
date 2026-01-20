import random #! para las cajas
from .models import *
from decimal import Decimal #para la multiplicacion, para que no tenga asi de que 1.000000001
import string #! estos son para generar el  codigo de rastreo random
import random 

def generar_caja(Envio_obj): #recibe un objeto de envio, vacio y lo llena

    caja = Envio_obj.suscripcion.caja
    valor_maximo = caja.monthly_price * Decimal('1.5')

    productos_posibles = list(Producto.objects.filter(categoria__in=caja.allowed_categories.all()))#genera una lista de los productos posibles



    if not productos_posibles: #SI NO HAY PRODUCTOS DE ESA CATEGORIA USAMOS DE CUALQUIERA COMO PLAN B
        #TODO que de un error en lugar de
        productos_posibles = list(Producto.objects.all())

    #ahora como tenemos la lista de productos de esa lista vamos a seleccionar aletoriamentem uejejejej 
    productos_seleccionados = [] #definimos la lista sino python se nos desconoce
    valor_acumulado = Decimal('0.00') #aca es donde vamos a comoparar para ver que no nos quedemos pobres con la caja kakakakka

    random.shuffle(productos_posibles) #hacemos un random de todos los productos posibles. que rico es el sexo por telepatia con enanos 
    #? shuffle reordena la lista de forma aleatoria
    for producto in productos_posibles:
        if len(productos_seleccionados) >= 3:
            break #ya ta hecho ahi dejemole el ddialbo papadio

        if (valor_acumulado + producto.valor) <= valor_maximo: #revisa si al meter este producto nos pasamos del presupuesto ya no lo mete, sino si
            productos_seleccionados.append(producto) #va a llenar productos hasta que tenga 3 o mas y ahi se acaba #todo que pasa si ya no hay
            valor_acumulado += producto.valor
    if len(productos_seleccionados) < 3:
        #* Calculamos cuantos productos faltan
        faltantes = 3 - len(productos_seleccionados) #// todo hay un error y es que al rellenar si es que falta con productos aleatorios sin filtrar en la categoria puede repetir objeto
        #sacamos una lista de los objetos,pero excluimos los que tengan las siguientes id, que son las de productos uqe ya se eligieron, para no repeti
        #? doble guion bajo es la condicion o puente __
        ids_usados = [p.id for p in productos_seleccionados]
        items_reserva = list(Producto.objects.exclude(id__in=ids_usados)) #esto es como lo del codewars, es el mismo cidigo que podrias hacer hacia abajo pero comprimido
            
        #el min compara 2 numeros para ver el mas pequenio. elige el mas peque;o, los que faltan, o los que tenemos si es que tenemos menos de los que faltan
        #que digamos oslo hay 2, el mas peque;o es 2 y pide 2, asi o se rompe el sa,ple, eso pq nos estaba dando un error el sample estupidito maldito python lo odio es lo mejor que existe gravias python por todo eres el mejor lenguaje del mundo python ojala nunca te remplazen si algun dia te vuelves obsoleto te seguire usando python, si me pudiera me casaria contigo ijueputa caca
        
        cantidad_k = min(faltantes, len(items_reserva)) #k es la variable del sample, agarramo el faltantes o si hay menos pues menos
        if cantidad_k > 0: #osea si tenemos items de reserva, sino pues ya sobate no hay nada base de datos para mala
            relleno = random.sample(items_reserva, cantidad_k)

            productos_seleccionados.extend(relleno)
            #valor_acumulado += producto.valor signoramos, la prioridad es tener 3 items y no mandarle con nada al usuario apra que no se cague en todo
    total_precio = sum([producto.valor for producto in productos_seleccionados])
    
    Envio_obj.productos.set(productos_seleccionados)
    Envio_obj.valor_total = total_precio
    Envio_obj.save() #sin el .save lo de arriba no sirve 
    #todo en el html mensaito con los items que uso
    

        #? random sample elige elementos random de una lista, el segundo argumento que toma es la cantidad de cosas que va a tomar
        # todo esto si es que no habia suficiente en la lista, en vez de agarrar segun la categoria agarra de todo, es un plan de emergencia si no tenemos nada, deberiamos mostrar un error en su lugar
        #// todo revisar que pasa si consigue meter objetos pero solo 1, pq en teoria pasaria esto, pero seeria un robo si solo mandamos un objeto
        #todo cantidad de productos dinamica

def generar_id_interno():
    # Genera un código tipo MYS-A1B2C3
    while True:
        caracteres = string.ascii_uppercase + string.digits
        codigo = ''.join(random.choices(caracteres, k=6))
        nuevo_codigo = f"MYS-{codigo}"
        
        # revisa que no se haya repetido el codigo, por si acaso y rompe el while
        if not Envio.objects.filter(codigo_rastreo_interno=nuevo_codigo).exists():
            return nuevo_codigo
        
#todo codigo secreto con la seccion de kamasutra
#todo decidir si se trabajara con suscriociones mensuales o solo una compra y ya 
\
#! ---------------------##################################################################################################
#! ---------------------##################################################################################################
#TODO ya se, mejor que sean compras unicas, pero tenga una suscripcion que desbloquea cajas adicionales y de descuentos
#! ---------------------##################################################################################################
#! ---------------------##################################################################################################