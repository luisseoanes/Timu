# Datos de demostración

Dos scripts siembran datos para ver el sistema con vida en local y en staging. Ninguno corre
fuera de `ENVIRONMENT=local` o `staging` (en staging, como se vacía y se vuelve a sembrar:
[despliegue de staging](despliegue-staging.md)), y los dos son repetibles.

```bash
docker compose exec api python -m scripts.datos_demo       # lo mínimo: ~1 min
docker compose exec api python -m scripts.operacion_demo   # ocho semanas de operación: ~5 min
```

## `datos_demo`: lo que piden las pruebas

`backend/scripts/datos_demo.py` deja lo que recorren las pruebas contra el stack
(`frontend/e2e-stack/`). El CI lo corre antes de esa suite. **Solo crea lo que falta**: no
actualiza lo ya sembrado, así que un stack viejo conserva los datos de cuando se sembró (ver
«Datos del día» en [la e2e contra el stack](frontend/e2e-stack.md)).

| Qué | Detalle |
| --- | --- |
| Equipo (clave `demo12345`) | Un usuario por perfil ([perfiles y permisos](perfiles-y-permisos.md)): `gerencia@timu.co`, `comercial@timu.co`, `atencion@timu.co`, `operaciones@timu.co` y `medico@timu.co`. Si ya existían con otro perfil (una base sembrada antes del 2026-11-19), pasan al suyo. El administrador `admin@timu.co` / `cambiar123` lo crea `inicializar` (en staging, con `ADMIN_PASSWORD_INICIAL`). |
| Clínica aliada | «Clínica Veterinaria del Norte», con un convenio y el usuario `aliada@timu.co`. |
| Portal de familias | `ana@example.com`, con el plan en pausa por cuotas vencidas, y `jorge@example.com`, al día: en cada pasada se le paga lo vencido. |
| Familias | Cinco, en Bogotá y Medellín, con sus mascotas y contratos (una sin plan). |
| Planes | Los beneficios provisionales: lo que dice el plegable 2026 donde lo dice y cupos de prueba en lo demás (`BENEFICIOS` y `DEL_PLEGABLE`), y la carencia y las exclusiones provisionales que dice el registro (`CONDICIONES`); ver [pendientes externos](pendientes-externos.md). |
| Agenda | Franjas de lunes a sábado, a domicilio y preventivas, en Bogotá y Medellín, y en la clínica solo en Medellín (la sede de Laureles, la única de TIMU; `FRANJAS_MEDELLIN`). |
| Portada pública (`R3-PUB-04`) | Lo que dice hoy la web de TIMU, como valores provisionales: los Datos de TIMU (presentación, visión, valores, clínica, horarios, teléfonos, el WhatsApp ficticio de local, correo, redes y la política de datos), las 17 aliadas de su página «Aliados» con su tipo, barrio, horario y orden en la red (sin logos), y los beneficios adicionales de cada plan. El contenido vive en `scripts/datos_portada.py`. A diferencia del resto, **sí se actualiza**: si los Datos de TIMU o los adicionales de un plan no coinciden con el fichero, se reescriben (las aliadas solo se crean si faltan). Ver [portada pública](portada-publica.md) y [pendientes externos](pendientes-externos.md). |
| Lo demás | Servicios, tareas, calendarios de preventivos (con una vacuna aplicada a Nala, de Laura Gómez, para que el barrido mida la verificación de un carnet real), una consulta firmada y un borrador, tres plantillas de consulta («Control general» y «Gastroenteritis leve», para cualquier atención, y «Otitis externa», para la consulta domiciliaria; `PLANTILLAS_CONSULTA`), una respuesta virtual aprobada, interesados, una conversación de WhatsApp que pide asesor, una plantilla y una campaña, y una remisión. |
| Ruta de la médica | En el primer día con cupo de la semana (no siempre hoy): los recorridos la buscan con `rutaDemo` (`e2e-stack/datos.ts`). |

## `operacion_demo`: ocho semanas de operación

`backend/scripts/operacion_demo.py`, después de `datos_demo`. Sirve para explorar el sistema
con historia (decidido con el usuario el 2026-11-16, `DEU-14`). Siembra:

- **Cartera en todos sus estados**: trece familias más, cada una con un perfil (al día, en mora,
  congelada, anual, trimestral por renovar, recién afiliada y dada de baja), sus cuotas emitidas
  y sus pagos con fecha y medio.
- **Rutas pasadas**: lunes, miércoles y viernes en Bogotá, martes y sábados en Medellín (con un
  médico propio, `medico.medellin@timu.co`). Cada ruta lleva sus visitas con la consulta
  firmada, y una de cada tres consultas parte de una plantilla de `datos_demo`; una de cada seis
  rutas omite una parada y una de cada siete cancela un servicio antes. Cada ruta lleva además una
  parada preventiva, que alterna vacuna y desparasitación: se agenda desde el preventivo, como en la
  bandeja, y al completarse lo aplica, así que el carnet sale de la ruta (6.8, 6.15).
- **Citas en la clínica**: los jueves, en Medellín, dos consultas clínicas y un control post
  atención, cada uno con su consulta presencial firmada.
- **Preventivos** aplicados en su fecha y otros vencidos, para la bandeja.
- **Encuestas** enviadas y respondidas, con las tareas que deja una calificación baja, y el
  **seguimiento post atención** de cada visita a los días que dice su configuración (6.21): la
  mayoría responde que su peludo sigue bien, algunas con una duda o una novedad que crea la tarea.
  Las configuraciones de encuesta se crean antes de recorrer las rutas, y los **recordatorios de
  preventivos** salen una vez, como el beat cada día (6.8).
- **Comercial**: interesados que llegaron en las últimas semanas, cada uno en su etapa (también
  perdidos). Los que llegan por WhatsApp escriben al asistente, como en la operación real: él los
  crea y su conversación se ve en la ficha.
- **Tareas** cerradas y abiertas vencidas, **remisiones** atendidas, anulada, vencida y por usar (la vencida, emitida hace 40 días, pasa a «Vencidas» la primera vez que corre `aliadas.vencer_remisiones`, a las 4:10),
  **orientaciones virtuales** cerradas y **una campaña** enviada hace tres semanas.
- **Atenciones de aliadas** (6.22) para la liquidación que ve Gerencia: la Clínica del Norte en
  Bogotá y dos aliadas de Medellín del catálogo, AnesVet y Centro Veterinario Buenos Aires, cada una
  con su convenio y su usuario (`aliada.anesvet@timu.co` y `aliada.buenosaires@timu.co`, clave
  `demo12345`). Atención al cliente emite cada remisión y la clínica reporta la atención por la API,
  repartidas en los últimos tres meses y también en el mes en curso.

- **Lo que ninguna pantalla tenía** (revisión del 2026-11-20, `complementos`): la configuración de
  encuestas con seguimiento post atención por tipo de servicio (6.20, 6.21), tres segmentos (6.16),
  un reporte semanal de Gerencia (Sección 8), dos contactos de Claudia Rincón y un examen subido a
  la ficha de Patricia Lozano (6.1), cuatro pendientes de consultas del médico de Bogotá (uno sin
  autorización, uno esperando, uno autorizado en gestión y uno rechazado; 6.6), un examen adjunto
  y una fórmula (6.14), el cambio de plan de Tom y el retiro de Oliver de la manada de Claudia
  (6.3), dos registros en línea, uno por pagar y otro pagado por transferencia (6.12), y **la agenda
  de los próximos 12 días** sin rutear: consultas a domicilio mientras las familias tengan cupo y,
  después, preventivos programados que se autorizan y se agendan como en la bandeja (6.5, 6.7, 6.8).
  Operaciones planea esas rutas y el médico las recorre mientras se prueba.

`datos_demo` registra además las plantillas de WhatsApp que envía la plataforma, con texto
provisional y aprobadas (`PLANTILLAS_DEMO`), salvo «Médico en camino», que queda sin registrar para
que Administración vea «Lo que falta configurar». Con ellas salen los avisos de mora, los
recordatorios de preventivos, la bienvenida y el seguimiento, y quedan en el historial de cada
familia.

Si su primera familia ya existe, no hace nada. Las aliadas de Medellín se pueden añadir a una base
que ya tenía la operación, sin vaciarla (una clínica con remisiones ya está sembrada):

```bash
docker compose exec -T -w /app api python -c "from datetime import datetime; \
from scripts import operacion_demo as op; from scripts.datos_demo import BOGOTA; \
op.aliadas_medellin(op.equipo(), op.dueno(), datetime.now(BOGOTA).date())"
```

Lo de la revisión del 2026-11-20, sobre una base ya sembrada (cada parte mira si ya está; la agenda
completa cada día hasta sus visitas): `datos_demo` otra vez, por las plantillas, y

```bash
docker compose exec -T -w /app api python -c "from datetime import datetime; \
from scripts import operacion_demo as op; from scripts.datos_demo import BOGOTA, Cliente, CLAVE_EQUIPO; \
op.complementos(op.equipo(), Cliente('medico@timu.co', CLAVE_EQUIPO), datetime.now(BOGOTA).date())"
```

Igual con los interesados de WhatsApp de una base sembrada antes del 2026-11-20, que se crearon a mano
y salían sin conversación: `op.conversaciones_por_whatsapp(op.equipo(), op.dueno())`.
 Para repetirla desde cero hace falta un stack
recién levantado (`docker compose down -v` o el proyecto de verificación del `CLAUDE.md` raíz).
Al terminar comprueba unos mínimos (`MINIMOS`) y sale con error si la siembra quedó corta: el CI
la corre después de la e2e del stack, para que no se rompa sin que nadie lo vea.

### Cómo se hizo: por la API, y después al pasado

La API no agenda en el pasado, y de los servicios cuelgan rutas, consultas, encuestas y
remisiones. Por eso:

1. **Todo se crea por la API, con sus reglas** (elegibilidad, cupos, transiciones, eventos).
   Cada día de operación se agenda y se recorre en un **día de reserva** futuro, el mismo día de
   la semana (las franjas van por día de la semana).
2. Al terminar ese día, sus fechas **se corren al pasado**, al día que le tocaba. Se hace día a
   día porque el cupo del mes cuenta los servicios futuros: corriéndolos enseguida, el cupo
   queda como si la visita hubiera sido en su fecha.
3. Al final se recalculan las marcas que la operación puso con la hora real (la llegada a una
   parada, la firma de la consulta, cuándo se agendó) a partir de la hora de cada visita.

Ese paso (y el de los preventivos aplicados en ruta) escribe con la conexión del **dueño del esquema** (la de `inicializar`): es la única que
puede fechar una consulta ya firmada. Nada más se escribe por debajo de la API.

Lo que el beat haría con el tiempo (emitir cuotas, revisar la mora, drenar el outbox, enviar
encuestas, lanzar campañas) el script lo llama en su propio proceso. Para eso importa al arrancar
los mismos módulos de tareas que el worker.

### Límites conocidos

- **Ningún interesado llega a «afiliado»**: esa etapa la pone la afiliación en línea al aprobarse
  el pago, y en local no hay pasarela de pruebas (Wompi, pendiente de TIMU). No se fuerza por SQL.
- **Las plantillas de WhatsApp** de campañas y encuestas se dan por aprobadas en local; en Meta
  siguen pendientes ([pendientes externos](pendientes-externos.md)).
- **Una visita preventiva aplica el preventivo con la fecha de hoy**: el script lo lleva al día de
  la visita, con su próxima fecha y la dosis siguiente (`aplicados_al_pasado`), escribiendo por
  debajo de la API como el resto del paso al pasado.

## Para ampliar cualquiera de los dos

- **Por la API**, como lo haría el panel. Lo que la API no permite no se fuerza por SQL.
- **Coherencia en el tiempo**: solo se visita o se remite a quien ya estaba afiliado ese día
  (`afiliada_desde`), y lo que nace de otra cosa (una tarea de una encuesta) lleva la fecha de su
  origen.
- **Cada ruta con su perfil** (Sección 12): los scripts hablan con la API como el equipo (`equipo()`
  en `datos_demo`), y cada petición sale con la sesión del perfil al que la ruta le toca, leído de
  las guardas de la propia API (`app/api/perfiles.py`). Los médicos llevan su propia sesión.
- **Los recorridos e2e buscan lo de `datos_demo` por su identidad** (un motivo, un nombre), nunca
  el primero de un listado: con la operación sembrada hay muchas más filas.
- **Una ampliación de `operacion_demo` añade su mínimo** a `MINIMOS`.
- **Se verifica en un stack limpio**: `datos_demo`, la e2e del stack, `operacion_demo` y otra vez
  la e2e. Los textos que ve el equipo llevan sus tildes; las ciudades se escriben como en el
  catálogo («Bogotá»).
