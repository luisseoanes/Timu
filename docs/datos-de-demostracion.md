# Datos de demostración

Dos scripts siembran datos para ver el sistema con vida en local. Ninguno corre fuera de
`ENVIRONMENT=local`, y los dos son repetibles.

```bash
docker compose exec api python -m scripts.datos_demo       # lo mínimo: ~1 min
docker compose exec api python -m scripts.operacion_demo   # ocho semanas de operación: ~5 min
```

## `datos_demo`: lo que piden las pruebas

`backend/scripts/datos_demo.py` deja lo que recorren las pruebas contra el stack
(`frontend/e2e-stack/`). El CI lo corre antes de esa suite. **Solo crea lo que falta**: no
actualiza lo ya sembrado, así que un stack viejo conserva los datos de cuando se sembró (ver
«Datos del día» en el `CLAUDE.md` raíz).

| Qué | Detalle |
| --- | --- |
| Equipo (clave `demo12345`) | `medico@timu.co`, `operaciones@timu.co`, `comercial@timu.co` y `gerencia@timu.co`, un administrador solo para los recorridos e2e. El administrador `admin@timu.co` / `cambiar123` lo crea `inicializar`. |
| Clínica aliada | «Clínica Veterinaria del Norte», con un convenio y el usuario `aliada@timu.co`. |
| Portal de familias | `ana@example.com`, con el plan en pausa por cuotas vencidas, y `jorge@example.com`, al día: en cada pasada se le paga lo vencido. |
| Familias | Cinco, en Bogotá y Medellín, con sus mascotas y contratos (una sin plan). |
| Planes | Los beneficios provisionales: lo que dice el plegable 2026 donde lo dice y cupos de prueba en lo demás (`BENEFICIOS` y `DEL_PLEGABLE`; ver [pendientes externos](pendientes-externos.md)). |
| Agenda | Franjas de lunes a sábado, a domicilio y preventivas, en Bogotá y Medellín. |
| Lo demás | Servicios, tareas, calendarios de preventivos, una consulta firmada y un borrador, una respuesta virtual aprobada, interesados, una conversación de WhatsApp que pide asesor, una plantilla y una campaña, y una remisión. |
| Ruta de la médica | En el primer día con cupo de la semana (no siempre hoy): los recorridos la buscan con `rutaDemo` (`e2e-stack/datos.ts`). |

## `operacion_demo`: ocho semanas de operación

`backend/scripts/operacion_demo.py`, después de `datos_demo`. Sirve para explorar el sistema
con historia (decidido con el usuario el 2026-11-16, `DEU-14`). Siembra:

- **Cartera en todos sus estados**: trece familias más, cada una con un perfil (al día, en mora,
  congelada, anual, trimestral por renovar, recién afiliada y dada de baja), sus cuotas emitidas
  y sus pagos con fecha y medio.
- **Rutas pasadas**: lunes, miércoles y viernes en Bogotá, martes y sábados en Medellín (con un
  médico propio, `medico.medellin@timu.co`). Cada ruta lleva sus visitas con la consulta
  firmada; una de cada seis omite una parada y una de cada siete cancela un servicio antes.
- **Preventivos** aplicados en su fecha y otros vencidos, para la bandeja.
- **Encuestas** enviadas y respondidas, con las tareas que deja una calificación baja.
- **Comercial**: interesados que llegaron en las últimas semanas, cada uno en su etapa (también
  perdidos).
- **Tareas** cerradas y abiertas vencidas, **remisiones** atendidas, anulada, vencida y por usar,
  **orientaciones virtuales** cerradas y **una campaña** enviada hace tres semanas.

Si su primera familia ya existe, no hace nada. Para repetirla desde cero hace falta un stack
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

Ese paso escribe con la conexión del **dueño del esquema** (la de `inicializar`): es la única que
puede fechar una consulta ya firmada. Nada más se escribe por debajo de la API.

Lo que el beat haría con el tiempo (emitir cuotas, revisar la mora, drenar el outbox, enviar
encuestas, lanzar campañas) el script lo llama en su propio proceso. Para eso importa al arrancar
los mismos módulos de tareas que el worker.

### Límites conocidos

- **Ningún interesado llega a «afiliado»**: esa etapa la pone la afiliación en línea al aprobarse
  el pago, y en local no hay pasarela de pruebas (Wompi, pendiente de TIMU). No se fuerza por SQL.
- **Las plantillas de WhatsApp** de campañas y encuestas se dan por aprobadas en local; en Meta
  siguen pendientes ([pendientes externos](pendientes-externos.md)).
- **Solo hay consultas a domicilio en las rutas.** Faltan vacunas y desparasitaciones en ruta, y
  controles y consultas en clínica (`DEU-14`), y las plantillas de consulta (`DEU-15`): ver la
  [deuda del rediseño](rediseno/deuda.md).

## Para ampliar cualquiera de los dos

- **Por la API**, como lo haría el panel. Lo que la API no permite no se fuerza por SQL.
- **Coherencia en el tiempo**: solo se visita o se remite a quien ya estaba afiliado ese día
  (`afiliada_desde`), y lo que nace de otra cosa (una tarea de una encuesta) lleva la fecha de su
  origen.
- **Cupo de peticiones por usuario**: los scripts trabajan con `admin@timu.co`,
  `operaciones@timu.co` y los médicos, nunca con `gerencia@timu.co` ni `comercial@timu.co`, que
  son de los recorridos e2e.
- **Los recorridos e2e buscan lo de `datos_demo` por su identidad** (un motivo, un nombre), nunca
  el primero de un listado: con la operación sembrada hay muchas más filas.
- **Una ampliación de `operacion_demo` añade su mínimo** a `MINIMOS`.
- **Se verifica en un stack limpio**: `datos_demo`, la e2e del stack, `operacion_demo` y otra vez
  la e2e. Los textos que ve el equipo llevan sus tildes; las ciudades se escriben como en el
  catálogo («Bogotá»).
