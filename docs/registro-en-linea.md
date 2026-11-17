# El registro en línea

Cómo se afilia una familia sin pasar por el equipo (requisitos 6.1 y 6.12: formulario → pago →
contrato → perfil, sin redigitar), de la ciudad al portal. Cruza tres dominios (`planes`,
`afiliaciones` y `publico`) y los dos lados (`backend/app/modules/afiliaciones/registro.py` y
`frontend/src/features/publico/`), y ninguno de los dos lo cuenta entero. La composición de las
pantallas está en [`DESIGN.md`](../DESIGN.md) («El registro en línea») y su historia en la
[hoja de ruta](hoja-de-ruta-rediseno.md) (`R3-PUB-02`).

## El recorrido

| Paso | Pantalla | API (`/api/v1/afiliaciones/registro…`) |
| --- | --- | --- |
| Ciudad | `/afiliacion`: «¿En qué ciudad vives?» y la confirmación de que solo se afilian perros y gatos | `GET /ciudades` |
| La manada | Una ficha por peludo (nombre, especie y su plan); el plan elegido abierto con lo que cubre y el comparador | `GET /planes?ciudad=` |
| El total | El resumen o la barra fija: «2 peludos · tarifa de 2» | `POST /cotizacion` (cada periodicidad) |
| Cómo pagar | «¿Cómo quieres pagar?»: periodicidad, a quién enviar el comprobante y las aceptaciones | `POST /contrato-modelo` (el PDF) |
| Pago | La pasarela de Wompi | `POST ""` (crea la solicitud y el pago; da el enlace y un token) |
| Regreso | `/afiliacion/resultado`: confirmando, rechazado, cerrado o activo | `POST /consulta` (cada 4 s mientras espera) y `POST /reintentar` |
| Datos de la familia | `/afiliacion/completar`: titular, otros contactos, cada peludo y la contraseña del portal | `POST /completar` |

Lo que lee cualquiera sin sesión: `GET /contacto` (el WhatsApp de TIMU, si está configurado).

## Lo que manda la API

- **Precio**: el mismo cálculo que cobra (`planes.cotizar`): cada peludo paga la tarifa de su plan
  para el número total de peludos (desde 4, la de 4), y el descuento por periodo largo solo existe
  con un peludo. El panel nunca suma: muestra lo que devuelve la cotización.
- **Lo que cubre cada plan**: `GET /planes` da cada beneficio con su nombre y en palabras (`texto`:
  «1 al mes», «2 al año · cubre el 40 %», «Sin tope de usos»), en el orden del catálogo, y las
  condiciones del plan (`carencia`, `exclusiones`, `terminos_url`) cuando Administración → Planes
  las escribió. Sin ellas, el registro no las inventa ni las muestra.
- **El contrato antes de pagar**: `POST /contrato-modelo` genera, sin guardar nada, el mismo
  contrato que se firma (`afiliaciones/documento.py`) con lo elegido y sin datos de la familia.
- **El estado del registro** (`/consulta`): `pendiente_pago` (esperando la pasarela, o rechazado si
  `estado_pago` lo dice), `pagada` (falta el formulario), `completada`, `cancelada` (no se pagó).
  `completar` puede dejarlo en revisión del equipo si la familia ya tiene un contrato vigente. La
  consulta nombra el plan de cada peludo con su color, para la manada de las páginas siguientes.

## El token y los plazos

- **El token** del registro vive en el `sessionStorage` de la pestaña que pagó
  (`frontend/src/features/publico/registro.ts`): no abre sesión y deja de valer al completar. Si la
  familia vuelve en otra pestaña u otro equipo, usa el enlace que se le envía por correo y WhatsApp.
- **Plazos** (`registro.py`): el enlace de pago vence a las 24 horas y, tras un rechazo, `reintentar`
  da otro pago a la misma solicitud; a las 24 horas de pagada se reenvía el enlace del formulario y a
  las 48 queda una tarea comercial; lo que no se paga se cierra a las 48 horas del último enlace, y a
  los seis meses se borra su contacto (Ley 1581).

## Lo provisional

Funciona entero, pero estos valores siguen pendientes de TIMU
([pendientes externos](pendientes-externos.md#valores-provisionales)): los precios, coberturas,
carencias y exclusiones de los planes, las condiciones generales del contrato y el WhatsApp de
contacto. Sin la pasarela de pruebas de Wompi el pago no se prueba de punta a punta: las pruebas
simulan la consulta del registro, y el recorrido contra el stack llega hasta el pago sin pagar.

## Dónde se prueba

- Backend: `tests/test_registro.py` (recorrido, plazos, modelo del contrato y contacto),
  `tests/test_planes.py` (condiciones y beneficios en palabras) y `tests/test_documentos.py`.
- Panel: `src/features/publico/registro.test.tsx`; `e2e/publicas.spec.ts` (sin desborde ni
  contraste insuficiente a 375 y 1280 px); `e2e-stack/recorridos.spec.ts` («una familia que se
  afilia», con el catálogo real).
