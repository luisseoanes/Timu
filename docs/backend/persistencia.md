# Backend: persistencia

Por qué la base de datos garantiza la integridad, los permisos y la auditoría, y cómo se trabaja con ello. Las reglas, en una línea cada una, están en [`backend/CLAUDE.md`](../../backend/CLAUDE.md),
que es lo que lee cada sesión de Claude Code; aquí está el detalle completo, con el porqué de cada
una. Si una regla cambia, cambia en los dos sitios a la vez. Las rutas de código son relativas a
`backend/`.

## Persistencia: la base garantiza, Python explica

Una regla nueva entra en una línea en `backend/CLAUDE.md` y con su detalle aquí. El plan con el que nació todo esto es un registro cerrado: [`docs/registros/plan-persistencia.md`](../registros/plan-persistencia.md).

Toda regla que PostgreSQL puede hacer cumplir se hace cumplir en PostgreSQL. Python valida
antes para devolver un mensaje claro, pero la regla definitiva está en la base: si Python se
equivoca, o alguien escribe por SQL, la base rechaza la operación. Solo se quedan
exclusivamente en Python las reglas que dependen de un servicio externo o de la hora actual.
El plan completo y su avance están en [`docs/registros/plan-persistencia.md`](../registros/plan-persistencia.md).

- **Dos roles de base de datos.** `timu` (`POSTGRES_USER`) es el dueño del esquema: solo lo
  usan Alembic y `inicializar`. `timu_app` lo crea la migración `0013`, sin superusuario ni
  `BYPASSRLS` ni permisos de DDL, y con él se conectan la API, los workers, los scripts **y
  las pruebas**. Con un rol privilegiado la base no aplica sus políticas, así que la API
  (`lifespan`), el worker (`worker_process_init`) y la suite (`conftest.py`) se niegan a
  arrancar si el rol conectado es superusuario o tiene `BYPASSRLS`. Una tabla nueva le llega
  a `timu_app` sola, por los permisos por defecto de la `0013`.
- **Cada transacción lleva el contexto de quién la hace.** `ContextoDb` (`rol`,
  `usuario_id`, `familia_id`, `clinica_id`, `request_id` y, para `publico`, `llaves`) vive en `session.info` y un listener
  `after_begin` lo fija con `set_config(..., true)` al empezar cada transacción: es local a
  ella, así que no se filtra a la siguiente petición que reutilice la conexión. `get_db`
  empieza en `"publico"`, `get_current_user` lo cambia al usuario y `get_alcance` añade la
  familia. `sesion_worker` y los scripts usan `SISTEMA`. Para cambiarlo a mitad de una
  transacción: `await db.run_sync(fijar_contexto, contexto)`. Sin contexto los ajustes
  quedan vacíos y lo que dependa de ellos se niega: se falla cerrado.
- **Todo conjunto cerrado es un enum de PostgreSQL.** Una columna que guarda un valor de
  una lista que fija el código (estado, tipo, canal, rol, prioridad…) se declara
  `mapped_column(EnumDb(MiStrEnum))`, nunca `String(n)`. Añadir, quitar o renombrar un valor
  exige su migración (`ALTER TYPE … ADD VALUE`, o recrear el tipo para quitar uno), escrita
  a mano porque el autogenerate no detecta cambios en los valores de un enum.
  `test_cada_enum_del_modelo_coincide_con_el_de_la_base` falla si el `StrEnum` y la base no
  tienen los mismos valores, y `test_ningun_conjunto_cerrado_queda_como_texto_libre` si una
  columna con nombre de conjunto (`estado`, `tipo`, `canal`…) sigue siendo texto, salvo las
  abiertas de `_ABIERTAS` con su motivo. Dos trampas: un enum ordena por su declaración, así
  que `aplicar_orden` y cualquier `ORDER BY` que deba ser alfabético usan `cast(col, String)`;
  y `case({...}, value=col)` compara con `varchar`, así que también lleva el `cast`. El valor
  por defecto va en Python (`default=`), no en un `server_default` que el modelo no declare.
  Un `CHECK` que use un valor recién añadido con `ADD VALUE` compara `estado::text`: el valor
  no se puede usar en la transacción que lo crea. Quitarlo en el `downgrade` exige soltar y
  recrear antes `tr_<tabla>_transicion_estado`, que depende de la columna.
- **Toda referencia a un catálogo es una clave foránea.** Una columna que guarda la
  ciudad, la especie, un plan, una plantilla o una regla (`ciudad`, `especie`, `*_codigo`)
  lleva `ForeignKey` a su catálogo, con `onupdate="CASCADE"` si apunta a un código o un
  nombre, para que una corrección en el catálogo se propague en vez de bloquearse. Las
  ciudades se guardan por nombre canónico (`ciudades.nombre` es único), con sus tildes desde la
  migración `0048` («Bogotá», «Medellín»): las pruebas y los scripts escriben ese nombre, y
  `catalogos.ciudad_valida` acepta también «bogota» y devuelve el canónico. Python sigue
  validando antes para dar el mensaje (`catalogos.ciudad_valida`).
  `test_toda_referencia_a_un_catalogo_tiene_llave_foranea` falla si falta una, salvo las de
  `_REFERENCIAS_SIN_LLAVE` con su motivo.
- **Las invariantes de cada fila son `CHECK` y las de «solo uno» son índices únicos.** Se
  declaran en el modelo, junto a sus columnas: `__checks__ = {"nombre": "expresión SQL"}`
  (rangos, formatos, importes no negativos, campos que exige un estado: «firmada ⇒ firma y
  diagnóstico», «pagada ⇒ cubre su valor») y `__unicos__ = {"nombre": (["columnas"],
  "condición" | None)}` («un contrato vigente por familia»). `_restricciones_de_la_tabla`
  las convierte en `ck_<tabla>_<nombre>` y `uq_<tabla>_<nombre>`. El autogenerate no detecta
  un `CHECK` nuevo en una tabla existente ni la condición de un índice parcial: su migración
  se escribe a mano, con la expresión copiada dentro, y antes se comprueba contra los datos
  (`SELECT count(*) … WHERE NOT (expresión)`). Comprobar y luego insertar no es una regla:
  deja una ventana a dos peticiones simultáneas. Un índice único parcial no es diferible,
  así que el código que retira la versión activa y activa otra hace `flush()` entre los
  dos pasos. `test_cada_check_y_cada_unico_del_modelo_estan_en_la_base` compara modelo y
  base en los dos sentidos. Teléfonos: E.164 con `+` en todas las tablas
  (`normalizar_telefono`); `telefono_whatsapp` quita el `+` solo al enviar a Meta.
- **Los cambios de estado los valida la base.** `app/transiciones.py` tiene el grafo de
  cada entidad con estado (servicios y pendientes los importa de su módulo); la tabla
  `transiciones_estado` guarda las mismas aristas y el trigger `validar_transicion`
  (`BEFORE UPDATE OF estado`) rechaza cualquier cambio que no esté en ella, con
  `check_violation`. La tabla solo la escribe el dueño del esquema: añadir una transición
  exige editar el módulo y escribir la migración que inserta la arista, y
  `test_los_grafos_de_la_base_son_los_del_codigo` falla si no coinciden o falta un trigger.
  Una entidad nueva con estado lleva su grafo, su trigger y su migración. Quedan fuera, con
  el motivo en el módulo, los estados que cambian por información externa o por decisión
  libre del equipo (mensajes, pagos, cuotas, afiliación, embudo, plantillas de Meta).
- **La auditoría la escribe la base.** Un modelo que herede `Auditable` lleva el trigger
  `tr_<tabla>_auditoria`, que con `auditar()` registra cada alta, edición, cambio de estado
  o borrado, también los hechos por SQL, con el usuario y la petición del contexto de la
  transacción. Python no escribe la bitácora: `auditoria` solo admite `SELECT` para
  `timu_app`, y un trigger rechaza cualquier `UPDATE` o `DELETE` que no venga del dueño. Lo
  que es constancia de algo no cambia una vez escrito (`INMUTABLES` en
  `app/core/auditoria.py`, trigger `inmutable()`), y una historia clínica firmada solo pasa
  a `corregida`. Un modelo `Auditable` o una tabla de `INMUTABLES` sin su trigger hace
  fallar `test_cada_tabla_auditable_e_inmutable_tiene_su_trigger`; añadir uno exige su
  migración con el `CREATE TRIGGER`.
- **Nada de negocio se borra.** `timu_app` solo tiene `DELETE` en las tablas de estado técnico
  de `BORRABLES` (`app/core/database.py`); los permisos por defecto ya no lo conceden a una
  tabla nueva. Una baja, una anulación o un reemplazo es un estado o una marca (`activo`,
  `reactivada_en`, `dada_de_baja_en`), y las colecciones de negocio no usan `delete-orphan`.
  El único borrado es la función `anonimizar_familia()` (habeas data, Ley 1581), que solo
  admite el contexto de un administrador y se niega con un contrato vigente: sustituye los
  datos personales y su rastro en la bitácora, conserva lo clínico y lo contable, y devuelve
  las claves de los ficheros que `familias.purgar_archivos` borra del almacenamiento después
  de confirmar. `test_anonimizar_no_deja_datos_personales` recorre todas las tablas: un dato
  personal nuevo lo borra esa función (con su migración) o su tabla va en `CONSERVAN_DATOS`
  con su motivo. En texto libre clínico solo se borran menciones (`borrar_menciones`).
  `test_la_aplicacion_solo_borra_estado_tecnico` falla si una tabla de negocio recupera
  `DELETE`. Una familia dada de baja no tiene contrato vigente, por los dos lados (migración `0027`):
  `tr_familias_baja_sin_contrato_vigente` rechaza marcar la baja con uno vigente, así que la
  baja completa cancela antes el contrato (`afiliaciones.ciclo.dar_de_baja`), y
  `tr_contratos_vigente_de_familia_activa` rechaza crear o reactivar uno para una familia que
  ya se fue.
- **Lo que ve y escribe cada perfil lo decide la base (RLS).** Toda tabla tiene RLS y cuatro
  políticas para `timu_app` (`p_<tabla>_<operación>`), generadas de la matriz de
  `app/core/permisos_db.py`: `PERMISOS` (perfil → tabla → `S`, `I`, `U`, `D` y `L`, que es
  bloquear con `FOR UPDATE` sin poder editar), `CONDICIONES` (las filas de `familia`,
  `aliada` y `publico`, y las sesiones propias del equipo) y `CATALOGOS`. Sin contexto, la base no
  devuelve nada. `sistema` lo tiene todo; los webhooks pasan a `sistema` tras validar la
  firma, y las rutas públicas con token de un solo uso (registro en línea), tras validarlo.
  Toda escritura lleva lectura, porque `INSERT … RETURNING` exige pasar la política de
  `SELECT`. Una ruta nueva, o una que pase a tocar otra tabla, exige actualizar la matriz y
  escribir la migración que regenera sus políticas; si no, la prueba de esa ruta falla
  porque la base niega el acceso. Esa migración no importa la matriz, la congela: se genera
  comparando `politicas(TABLAS)` con las expresiones de la última migración de RLS, y lleva
  la anterior y la nueva de cada política cambiada para que el `downgrade` restaure la
  anterior (patrón de la `0026`). Para derivar lo que toca una ruta:
  `TIMU_REGISTRO_ACCESOS=<fichero> pytest` anota cada perfil, ruta, operación y tabla, con
  una sesión propia por petición para que ninguna lectura se sirva de memoria. En ese modo
  `test_pedir_asesor_con_contexto_y_el_bot_se_calla` falla siempre (lo que escribe el webhook
  queda en otra sesión) y pasa en la suite normal: no es un fallo. Ojo con los
  efectos: cambiar el estado de un servicio ejecuta reglas configurables que crean tareas y
  mensajes, y quien cambia ese estado tiene esos permisos aunque hoy ninguna regla los use.
  `test_toda_tabla_tiene_rls_y_las_politicas_de_la_matriz` compara cada política con lo que
  genera hoy la matriz, a través de su comentario. `restringir()` sigue en Python como
  segunda capa y para responder 404, y lo que filtra columnas (la vista por perfil de la
  historia clínica) también sigue en Python: RLS filtra filas.
- **`publico` solo ve las filas de quien declara la petición.** Es el perfil de toda petición
  sin sesión y del comienzo de cada petición autenticada, hasta que `get_current_user`
  reconoce al usuario. Sin llaves no ve nada. El código fija las llaves con
  `acotar_publico(db, …)` (`LLAVES_PUBLICAS` en `app/core/database.py`), donde ya conoce el
  valor y con el mismo valor que usa la consulta: el email o el teléfono de ingreso, el hash
  del token, el documento del formulario, el token de la encuesta, el código del carnet. Hay
  dos llaves de cuenta distintas: `usuario` (identificada, basta para enviarle un enlace) y
  `autenticado` (probó una credencial). Solo `autenticado` abre una sesión o cambia la
  contraseña, y un token de renovación reutilizado solo da `revocar`. Una ruta pública nueva,
  o una que pase a leer otra fila, declara sus llaves y amplía la condición de `publico` en la
  matriz (`CONDICIONES` admite una expresión por operación). Ojo: una lectura que la base
  filtra no da error, devuelve menos filas, y el código que trata ese dato como opcional sigue
  adelante con un resultado peor (así se detectó la encuesta que nombraba al profesional como
  «sin asignar»). Vale también para los catálogos: un perfil que no tiene la tabla en
  `PERMISOS` la lee vacía (pasó con `especies` a la aliada y, hasta el 2026-11-20, a Gerencia y a
  Operaciones, que veían «canino» y un selector de especie sin opciones; ahora lo vigila
  `test_todo_perfil_del_equipo_lee_los_catalogos_enteros`). Una escritura negada sí falla, con un
  500, pero solo la ve una prueba que llame la ruta por la API con su perfil: las del servicio
  corren como `sistema` (así se escapó la cuota de ajuste del cambio de plan, que Atención no
  podía crear). Para buscarlos: contar cada `SELECT` de `publico` también como `sistema` en
  la misma transacción (`SAVEPOINT`, `set_config('app.rol', 'sistema', true)`, `ROLLBACK TO`)
  y anotar las sentencias en que `publico` ve menos filas. Lo que necesite ver lo de todos,
  como el reparto por carga de los comerciales, va en una función `SECURITY DEFINER` que solo
  devuelve el resultado (`comercial_con_menos_carga()`). Límite: el contexto se fija con
  `set_config`, así que esto protege de errores de la aplicación, no de quien ejecute SQL
  arbitrario con su conexión.
- **Lo que crece con el negocio se consulta por índice.** Toda clave foránea lleva
  `index=True` (`test_toda_llave_foranea_tiene_indice`).
  `test_los_caminos_calientes_no_recorren_tablas_enteras` recorre los listados del panel y
  todas las tareas del beat, captura cada sentencia y la analiza con
  `EXPLAIN (GENERIC_PLAN)` y `enable_seqscan = off`. Si aun así una tabla que crece con el
  negocio se recorre entera, ningún índice sirve esa consulta y la prueba falla. Un listado
  o una tarea nueva se añade a `_LISTADOS` (uno de la clínica aliada, a `_LISTADOS_DE_ALIADA`, que se
  recorre con una sesión de aliada), o entra sola si es del beat. Para ordenar de lo más reciente a
  lo más antiguo sin índice en `created_at`, se ordena por `id`: es UUIDv7, sigue el orden de creación y
  usa la clave primaria (la bandeja de remisiones). Las tablas acotadas
  por naturaleza van en `_ACOTADAS`, y los procesos por lotes que leen casi toda la tabla a
  propósito en `_RECORRIDOS_A_PROPOSITO`, siempre con su motivo. Ordenar por una expresión
  (`CASE`) impide usar un índice: la bandeja de tareas ordena por el enum `prioridad`, cuyo
  orden de declaración es el de urgencia.
- **Límites y pool.** `timu_app` tiene `statement_timeout` de 30 s, `lock_timeout` de 10 s e
  `idle_in_transaction_session_timeout` de 60 s (migración `0024`). En compose, API, worker y
  beat llegan a la base por PgBouncer en modo transacción (`APP_DB_HOST`); el contexto de RLS
  es local a la transacción, así que no se cruza entre clientes, y asyncpg necesita
  `MAX_PREPARED_STATEMENTS`. Las migraciones e `inicializar` van directo. `db` precarga
  `pg_stat_statements` y registra en el log las consultas de más de 500 ms. Los límites se
  comprueban con una conexión de `timu_app` o en `pg_db_role_setting`: tras
  `SET ROLE timu_app`, `SHOW statement_timeout` da 0, porque los ajustes del rol solo se
  cargan al iniciar sesión.
- **Toda clave primaria es UUIDv7** (RFC 9562), con tres capas: `UUIDMixin` lo genera en
  Python (`nuevo_id()`, de `uuid-utils`, porque Python 3.12 no trae `uuid7`), la columna
  tiene `DEFAULT uuidv7()` para quien inserte por SQL, y `ck_<tabla>_id_uuidv7` rechaza
  cualquier otra versión. El `CHECK` lo añade un evento de mapper a nivel de tabla: a nivel
  de columna, el autogenerate de Alembic lo descartaría. Todo modelo hereda `UUIDMixin`, y
  `test_toda_tabla_tiene_id_uuidv7_generado_y_exigido_por_la_base` falla si una tabla no
  cumple. `nuevo_id()` solo se llama cuando el ID hace falta antes del `flush`. Lo que deba
  ser imposible de adivinar (referencias de pago, claves de almacenamiento, tokens) sigue
  usando `uuid4` o `secrets`: un v7 revela la fecha de creación.
