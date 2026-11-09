# Deuda: el ciclo entre ocho dominios del backend

**Cerrada el 2026-11-10.** Ya no hay ningún ciclo entre dominios del backend y
`CICLOS_CONOCIDOS` (`backend/tests/test_arquitectura.py`) está vacío: la guarda sigue
impidiendo que aparezca uno nuevo. Este documento queda como registro: el diagnóstico y el
plan, tal como se ejecutaron, y al final lo que hubo que hacer además.

Registrado el 2026-11-09, en la auditoría de [estándares de calidad](estandares-calidad.md);
plan revisado el 2026-11-10 contra el código (ver «Correcciones» al final).

## Resultado

| | Antes | Después |
| --- | --- | --- |
| Dominios en un ciclo | 8 (11 antes de la auditoría) | 0 |
| Entradas de `CICLOS_CONOCIDOS` | 21 | 0 |
| `familias` depende de | `archivos`, `auth`, `cartera`, `catalogos`, `comercial`, `planes`, `preventivos` | `archivos`, `auth`, `catalogos` |
| `planes` depende de | `auth`, `cartera`, `catalogos`, `familias`, `reglas` | `auth`, `catalogos`, `reglas` |

Ninguna ruta, código de respuesta ni mensaje cambió: el OpenAPI conserva los mismos
`operationId` y etiquetas, y `frontend/src/types/api.ts` regenerado sale idéntico.

## Lo que se hizo además del plan

- **Triggers en la base** (migración `0027`). Al salir la cancelación del contrato de
  `familias.dar_de_baja`, esa función ya no garantizaba sola que una familia dada de baja no
  quedara cobrable. Ahora la base hace cumplir «familia dada de baja ⇒ sin contrato vigente»
  por los dos lados: `tr_familias_baja_sin_contrato_vigente` rechaza marcar la baja con uno
  vigente, y `tr_contratos_vigente_de_familia_activa` rechaza crear o reactivar uno para una
  familia que ya se fue (antes solo lo frenaba Python en `cartera.crear_contrato`, y el estado
  del contrato no tiene grafo, así que un `UPDATE` podía reactivar uno cancelado).
  `test_una_familia_dada_de_baja_no_tiene_contrato_vigente` cubre los dos y falla sin la
  migración.
  Tres pruebas daban de baja una familia con contrato llamando a `familias.dar_de_baja` y
  esperando la baja completa (la regresión de la revisión F1 en `test_cartera.py` y las
  preparaciones de `test_campanas.py` y `test_dashboard.py`): el trigger las frenó, que era lo
  correcto, y pasaron a llamar a `afiliaciones.ciclo.dar_de_baja`.
- **El formulario público también da de alta mascotas.** Con una familia que ya existía,
  `desde_formulario` agregaba sus mascotas nuevas con la validación del plan y el calendario
  preventivo. Esa alta orquestada se le inyecta (`agregar_mascota=`), como los respondedores
  de `comunicaciones`, para no perderla al sacar la orquestación de `familias`.
- **El alta de mascota va en dos pasos** (`familias.nueva_mascota` e
  `incorporar_mascota`): el contrato se recalcula con la mascota nueva todavía sin guardar,
  para poder rechazarla sin escribir nada. Unir los dos pasos habría cambiado ese orden.
- **El cambio de plan** pasó a `cartera/router.py` en un router con `prefix="/planes"`, para
  conservar `POST /api/v1/planes/contratos/{id}/cambio`.
- Variables locales llamadas `contratos` en `cartera/service.py` tapaban al módulo nuevo;
  Ruff detectó una (F823) y se renombraron las tres.

El plan original sigue debajo, sin cambios.

## Qué está enredado

`cartera`, `clinica`, `comercial`, `familias`, `ia`, `planes`, `preventivos` y `servicios`
forman una sola componente: desde cualquiera de ellos se llega a cualquier otro siguiendo
imports. Son 21 aristas, pero **la mayoría van en la dirección correcta** (un dominio de
arriba que lee a uno de abajo, como `servicios` leyendo `Familia`). El ciclo lo cierran
solo cinco:

| Arista que cierra el ciclo | Dónde | Qué hace |
| --- | --- | --- |
| `familias → cartera` | `familias/service.py:161` (`dar_de_baja`), `:412` (`anonimizar`) | Cancela el contrato al dar de baja la familia; comprueba que no haya contrato vigente antes de anonimizar. |
| `familias → planes` | `familias/service.py:162` (`dar_de_baja`), `:247` (`_validar_contra_plan`), `:273` (`dar_de_baja_mascota`), `:413` (`anonimizar`, `VIGENTES`) | Busca el contrato vigente, valida que la mascota nueva quepa en el plan y recalcula el valor por mascotas al dar de alta o de baja una. |
| `familias → preventivos` | `familias/service.py:237` (`agregar_mascota`) | Crea el calendario preventivo de la mascota que entra a un plan vigente (F1-AFI-03). |
| `familias → comercial` | `familias/service.py:329` (`desde_formulario`) | Deja al interesado del formulario público en el embudo comercial (F3-COM-01). |
| `planes → cartera` | `planes/service.py:14-15`, `planes/router.py:174` | `planes` opera sobre `Contrato` y `Cuota`, que son de `cartera`: contrato vigente, ajuste por mascotas, cambio de plan con prorrateo y cuotas de ajuste. |

### La causa de fondo, en dos frases

1. **`familias` orquesta casos de uso que no son suyos.** Dar de baja una familia, dar de
   alta o de baja una mascota, anonimizar y recibir un formulario tocan contrato, plan,
   preventivos y embudo comercial. `familias` debería ser la ficha (titular, mascotas,
   ubicación) y estar abajo del todo; hoy llama hacia arriba.
2. **`planes` mezcla el catálogo con la vida del contrato.** El catálogo (plan, beneficios,
   especies, recomendar, validar) es de `planes`; todo lo que lee o escribe `Contrato` y
   `Cuota` es de `cartera`, que es dueña de esos modelos.

## Cómo romperlo, en orden

Dos pasos, **en este orden**, cada uno en un commit `refactor(...)` en verde por sí solo y
sin cambiar nada observable: mismas rutas, mismos códigos de respuesta y mismos mensajes.
Simulado sobre el grafo real con las funciones de la guarda, contando las aristas que cada
paso quita **y las que añade**:

| Estado | Dominios en ciclo | Entradas de `CICLOS_CONOCIDOS` |
| --- | --- | --- |
| Hoy | 8 | 21 |
| Tras el paso 1 | 2 (`cartera`, `planes`) | 2: `cartera → planes` y `planes → cartera` |
| Tras el paso 2 | 0 | 0 |

**Por qué no al revés.** Si primero se lleva el contrato a `cartera`, los que hoy llaman a
`planes.contrato_vigente` desde dentro del ciclo (`clinica`, `preventivos`, `servicios`)
pasan a importar `cartera`, que sigue en el ciclo: son aristas nuevas que lo cierran, y
`test_ninguna_dependencia_nueva_entre_dominios_cierra_un_ciclo` pone el commit en rojo. Para
pasarlo habría que *añadir* entradas a la lista. En este orden, el paso 1 solo añade aristas
desde `afiliaciones`, que está fuera del ciclo, y cuando llega el paso 2 ya no queda ciclo
que cerrar.

### Paso 1. Los casos de uso de la familia afiliada salen de `familias`

`afiliaciones` ya depende de `cartera`, `familias`, `planes`, `preventivos` y `comercial`,
ningún dominio la importa y no está en el ciclo: es el orquestador natural. Se crea
`afiliaciones/casos.py` (o se amplía su `service.py`) con:

| Caso de uso | Hoy (`familias/service.py`) | Después |
| --- | --- | --- |
| Baja de la familia | `dar_de_baja` busca el contrato vigente, lo cancela y marca la familia | El orquestador busca el contrato y lo cancela (`cartera.cancelar`, que ya pasa la familia a `cancelada`); `familias.dar_de_baja` solo comprueba y anota la baja |
| Alta de mascota | `agregar_mascota` valida contra el plan, ajusta el valor y crea el calendario | El orquestador valida la especie contra el plan del contrato vigente, llama a `familias.agregar_mascota`, ajusta el valor y crea el calendario (`preventivos.calendario_inicial`) |
| Baja de mascota | `dar_de_baja_mascota` recalcula el valor | `familias.dar_de_baja_mascota` marca la baja; el orquestador recalcula |
| Anonimizar | `anonimizar` consulta `Contrato` antes | El orquestador comprueba el contrato vigente con el mismo `ReglaNegocio` («Cancele el contrato vigente…», 422) y llama a `familias.anonimizar`, que ya no importa `cartera` |
| Formulario público | `desde_formulario` crea o completa la ficha y registra al interesado | El orquestador llama a `familias` para la ficha y a `comercial.registrar` |

- **Los endpoints se mueven con el caso de uso.** Si `familias/router.py` llamara al
  orquestador, la guarda contaría `familias → afiliaciones` y aparecería un ciclo nuevo. Los
  cinco endpoints (`familias/router.py:97` baja, `:111` anonimizar, `:142` alta de mascota,
  `:166` baja de mascota y `:202` formulario) pasan a `afiliaciones/router.py`, que hoy solo
  tiene `prefix="/afiliaciones"`: se le añaden routers con `prefix="/familias"`,
  `"/mascotas"` y `"/formularios"`, como ya hace `familias/router.py:29-31`, y se registran en
  `app/api/v1/router.py`. Mismas rutas, mismos `tags` y mismas `dependencies`: el panel, el
  OpenAPI y `frontend/src/types/api.ts` no cambian (comprobarlo regenerando los tipos: el
  diff debe salir vacío).
- `afiliaciones/router.py:89` ya llama a `familias.desde_formulario`: pasa a llamar al
  orquestador.
- **Por qué no la base para anonimizar.** `anonimizar_familia()` (migración `0022`) también
  se niega con contrato vigente, pero lanza el mismo `check_violation` que para «ya
  anonimizada», y el manejador genérico de `IntegrityError` responde 409 con un mensaje que no
  dice cuál de los dos fue. Distinguirlos parseando el texto de PostgreSQL es frágil, y
  `test_anonimizar_dos_veces_o_con_contrato_vigente` exige 422 y «contrato vigente». La
  comprobación en la base se queda como segunda capa.
- **Síncrono a propósito.** La tentación es convertir estos efectos en eventos del outbox.
  Para el calendario preventivo y el embudo comercial sería aceptable (llegarían un minuto
  después). Para cancelar el contrato y validar el plan **no**: la validación tiene que poder
  rechazar el alta con un 422 en la misma petición, y una baja que no cancela el contrato en
  la misma transacción deja una ventana en la que la familia sigue cobrable.
- Al terminar, la suite pide borrar 19 entradas: todas salvo `("cartera", "planes")` y
  `("planes", "cartera")`. `familias` deja de importar `cartera`, `planes`, `preventivos` y
  `comercial`.

### Paso 2. La vida del contrato pasa de `planes` a `cartera`

Mover a `cartera` (a un `cartera/contratos.py` nuevo, para no inflar `cartera/service.py`):
`VIGENTES`, `contrato_vigente`, `_mascotas_activas`, `calcular_cupo`, `valor_mensual`,
`ajustar_por_mascotas`, `cambiar_plan` con `_ciclo_actual`, `_cargar_ajuste` y `_aplicar`, y
`aplicar_cambios_programados`: unas 230 líneas de `planes/service.py:64-296`. El endpoint
`POST /contratos/{id}/cambio` pasa de `planes/router.py:169` al router de `cartera`, con la
misma ruta.

- Quita `planes → cartera` y `planes → familias`: lo que hoy lee `Familia` o `Mascota` en
  `planes` es justo lo que se mueve. `planes` queda dependiendo de `auth`, `catalogos` y
  `reglas` (la recomendación de planes sigue usando reglas).
- Coste: `contrato_vigente` y `calcular_cupo` cambian de import en `afiliaciones` (ya con el
  orquestador del paso 1), `aliadas`, `campanas`, `cartera`, `clinica`, `portal` (router y
  service), `preventivos` y `servicios`. En las pruebas hay 8 llamadas directas a funciones
  que se mueven, en `test_planes.py` (4), `test_cartera.py` (2), `test_campanas.py` y
  `test_dashboard.py`; el resto pasa por HTTP y no cambia.
- La suite pide borrar las dos entradas que quedan. `CICLOS_CONOCIDOS` se deja como
  diccionario vacío: la guarda sigue impidiendo ciclos nuevos.
- Aparte y opcional: `dinero`, `centavos` y `formato_cop` de `cartera/periodos.py` son
  formato de moneda, no reglas de cartera. Llevarlos a `app/core/dinero.py` quita
  `comercial → cartera`, que solo los usa para el bot. No afecta al ciclo.

### Al cerrar

Borrar la entrada de deuda de modularidad en [estándares de calidad](estandares-calidad.md)
y dejar este documento como registro con la fecha de cierre, o borrarlo.

## Lo que hay que vigilar

- **Las pruebas que más cubren estos casos**: `test_familias.py`, `test_planes.py`,
  `test_cartera.py`, `test_afiliaciones.py`, `test_preventivos.py` y `test_portal.py`. No
  deberían cambiar más que los imports; si una prueba de comportamiento necesita otro
  cambio, el refactor ha cambiado algo observable.
- **Permisos**: un endpoint que cambia de router conserva sus `dependencies` de perfil;
  `test_permisos.py` compara la matriz completa y falla si cambia. La matriz de RLS
  (`app/core/permisos_db.py`) depende del perfil y la tabla, no del módulo Python que hace
  la consulta: mover código no la toca.
- **Imports diferidos**: casi todas estas aristas eran imports dentro de funciones, puestos
  para esquivar el import circular. Cerrados los ciclos, los 106 imports de `app` que
  quedaban dentro de funciones subieron a la cabecera (2026-11-10), y
  `test_los_imports_de_la_aplicacion_van_en_la_cabecera` impide que vuelvan.

## Correcciones respecto a la primera versión (2026-11-09)

- El orden estaba invertido (contrato primero): ese orden pone en rojo la guarda de ciclos
  nuevos en el primer commit. La primera simulación solo quitaba aristas y no contaba las
  que añade cada paso.
- Para anonimizar proponía traducir el error de la base; no distingue los dos motivos y
  cambiaría el 422 por un 409.
- Decía que `portal` llamaba a estos casos de uso: no lo hace. El único llamador fuera de
  `familias` es `afiliaciones/router.py:89`.
