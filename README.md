MVP
PRODUCTO MINIMO VIABLE


1. Módulo Público y Tienda 

    Catálogo de Cajas: Página principal que muestra las tarjetas con los diferentes tipos de cajas (ej: "Caja Gamer", "Caja Otaku") y sus precios.

    Detalle de Caja: Vista individual de cada caja que muestra su descripción detallada, las categorías de productos que puede contener y el botón de "Suscribirse".

    Simulación de Compra: Al hacer clic en "Suscribirse", el sistema crea la suscripción automáticamente (sin pasarela de pago real) y redirige al usuario a una página de éxito.

2. Módulo de Usuarios 

    Registro de Usuarios: Formulario para que nuevos visitantes creen su cuenta.

    Inicio/Cierre de Sesión: Sistema de login estándar de Django.

    Mi Perfil: Un panel privado donde el usuario puede ver:

        Su plan actual (ej: "Suscripción Activa: Caja Gamer").

        Fecha del próximo pago.

        Historial de Envíos: Lista de las cajas que el sistema le ha "enviado" y qué productos le tocaron en cada una.

3. Módulo de Administración 

    Gestión de Planes (Cajas): El administrador puede crear tipos de cajas (ej: "Caja Premium - $50") y definir qué categorías de productos permite (ej: Solo "Tecnología" y "Ropa").

    Gestión de Inventario (Productos): CRUD completo para añadir productos (Items), asignarles una categoría (ej: "Funko Pop" -> "Coleccionables") y definir su stock inicial.

    Gestión de Suscripciones: El administrador puede ver quién está suscrito y cancelar suscripciones manualmente si es necesario.

4. Lógica de Negocio 

    Generador de Envíos Aleatorios: Una función (disparada manualmente desde el admin) que:

        Detecta todas las suscripciones activas.

        Selecciona 3 productos al azar del inventario que coincidan con la categoría de la caja del usuario.

        Resta el stock de esos productos.

        Guarda el registro en el historial del usuario.