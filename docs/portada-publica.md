# La portada pública

La raíz de `timu.com.co` (`/`) y la página de cada plan (`/planes/<plan>`): el punto de acceso a todo
(afiliarse, el portal de familias, el panel del equipo y el de la clínica aliada) y lo que decía la
web de WordPress que sustituye. Cruza cinco dominios (`planes`, `aliadas`, `institucional`,
`comercial` y `publico`) y los dos lados, y ninguno de los dos lo cuenta entero. La composición está
en [`DESIGN.md`](../DESIGN.md) («La portada pública y la página de cada plan»), las decisiones en su
contrato (`.impeccable/surfaces/frontend-src-features-publico-portadapage-tsx.md`) y su historia en
la [hoja de ruta](hoja-de-ruta-rediseno.md) (`R3-PUB-04`).

## De dónde sale cada cosa

Nada de lo que dice la portada está escrito en el panel: todo lo edita Administración y lo lee la
API pública, sin sesión.

| Sección | Lo que muestra | Lo escribe | API pública |
| --- | --- | --- | --- |
| Primera pantalla | Las fotos del equipo, los planes en su color con lo menos que paga un peludo y «Arma tu plan» (ciudad, perros y gatos) | Administración → Planes (tarifas y color) | `GET /afiliaciones/registro/ciudades` y `/planes?ciudad=` |
| Planes | El comparador: precio, cada servicio, los adicionales y las condiciones | Administración → Planes: cada beneficio con su tope por episodio, carencia y detalle, y el bloque «Beneficios adicionales» | `GET /afiliaciones/registro/planes?ciudad=` |
| La red TIMU | Una estación por barrio, la clínica de TIMU como intercambio, el ramal a casa y los servicios sin sede | Administración → Aliadas, bloque «En la portada» de cada una (si sale, tipo, 24 horas, barrio, horario, presentación, orden y logo) | `GET /aliadas/publicas` |
| Quiénes somos y el pie | Presentación, misión, visión, valores, razón social y NIT | Administración → Datos de TIMU | `GET /institucional` |
| Contacto | WhatsApp, teléfonos, correo, la clínica, horarios, redes y el formulario | Administración → Datos de TIMU | `GET /institucional` y `POST /comercial/contacto` |
| Cada plan | Su línea con un servicio por estación, lo que cubre, los adicionales, lo que paga por peludos y por adelantado en cada ciudad y sus condiciones | Administración → Planes | `GET /afiliaciones/registro/planes?ciudad=` |

Una sección sin datos no se inventa: un campo de Datos de TIMU vacío no se muestra, sin aliadas en
la portada no hay red, y en una ciudad sin planes se dice «Aún no vendemos planes en esta ciudad».

## Lo que manda la API

- **Las reglas de la red** (`redTimu`, `frontend/src/features/publico/portada.ts`): las aliadas salen
  en el orden de Administración, y las seguidas del mismo barrio comparten estación. Un municipio
  sin barrios en la red es una estación; en uno que ya los tiene, una aliada sin barrio va con los
  servicios. Los especialistas, la farmacia y la funeraria no tienen sede abierta y van aparte. La
  clínica de TIMU es la estación cuyo barrio aparece en el suyo («Los Conquistadores, Laureles» está
  en «Laureles»), o una propia al principio. El ramal a casa sale si algún plan trae
  `consulta_domiciliaria`.
- **El precio**: lo menos que paga un peludo al mes con los peludos de la familia (desde 4, la
  tarifa de 4), de las tarifas del catálogo; el total exacto lo da después la cotización del
  registro.
- **Del contacto a Comercial**: `POST /comercial/contacto` crea o actualiza el interesado (origen
  «web»), guarda el mensaje (los últimos veinte, en `datos.mensajes_web`) y la autorización de datos
  con su texto y su fecha, y deja la tarea «Responder el mensaje de la web de…». Exige celular o
  correo; con el campo trampa lleno responde lo mismo y no guarda nada. La ficha del interesado en
  Comercial muestra lo que escribió.
- **A la afiliación con lo elegido**: «Ver mis planes» y «Afiliar a mi peludo con…» abren
  `/afiliacion?ciudad=…&perros=…&gatos=…&plan=<id>`, y el registro arranca con esa manada.

## Las direcciones

- **El panel del equipo vive en `/panel`**; sus direcciones viejas (`/familias/…`, `/cartera`…)
  llevan a `/panel/…` (`AlPanel`, `src/routes/modulos.ts`).
- **La web de WordPress** (`DeLaWebVieja`, `src/routes/WebVieja.tsx`): `/planes/`, `/aliados/`,
  `/nosotros/` y `/contactanos/` llevan a su sección de la portada (`/#planes`, `/#aliadas`…), y
  `/service/plan-<plan>/` a `/planes/<plan>`. La ruta de un plan es su código con guiones
  (`colita_feliz` → `/planes/colita-feliz`).
- **`/` es pública por comparación exacta** en `PAGINAS_PUBLICAS` (`src/api/client.ts`): como
  prefijo, lo sería todo.

## Lo provisional

En local, `datos_demo` siembra lo que dice hoy la web de TIMU (`backend/scripts/datos_portada.py`,
ver [datos de demostración](datos-de-demostracion.md)). Desplegado, todo empieza vacío y lo escribe
Administración. **Antes de publicarla en el dominio** hace falta lo de TIMU, en
[pendientes externos](pendientes-externos.md): confirmar esos valores (la misión está cortada, el
horario de los sábados se contradice), las aliadas vigentes y sus logos, el permiso de las personas
de las fotos del equipo, la licencia de las fotos de las piezas impresas, el WhatsApp real y volver
a alojar la política de datos, cuyo enlace actual muere con WordPress. Las fotos y su procedencia:
`frontend/src/assets/portada/README.md`.

## Dónde se prueba

- **Vitest**: `frontend/src/features/publico/portada.test.tsx` (la red, los precios, «Arma tu plan»,
  el contacto y la página del plan), `registro.test.tsx` (el registro con la manada de la portada),
  `src/routes/WebVieja.test.tsx` y `src/api/client.test.ts` (`/` y `/planes` públicas). En
  Administración, `planes-adicionales.test.tsx`, `datos-timu.test.tsx` y
  `aliadas-en-portada.test.tsx`.
- **Backend**: `test_institucional.py`, `test_aliadas.py` (las públicas y el logo) y
  `test_comercial.py` (el contacto de la web).
- **Contra el stack**: el barrido responsive mide `/` y `/planes/:plan`, y un recorrido va de la
  portada al registro con la manada armada y de la dirección vieja de un plan a su página
  (`e2e-stack/recorridos.spec.ts`).
