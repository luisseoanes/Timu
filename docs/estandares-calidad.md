# Estándares de calidad: qué se exige y qué lo comprueba

Las secciones 3 y 4 del [documento de requerimientos](documento-requerimientos-funcionales.md)
piden una solución **modular, escalable y preparada para crecer sin reemplazar su base**, y
que garantice escalabilidad, seguridad, integridad de la información, trazabilidad,
interoperabilidad, capacidad de integración y sostenibilidad tecnológica.

Dicho así no se puede verificar. Este documento traduce cada estándar a reglas concretas y
dice qué prueba o paso del CI falla si se incumplen. **Una regla sin guarda es una
intención**: aquí solo entran las que algo hace cumplir, y lo que todavía no cumple va en la
columna de deuda, con nombre, en lugar de darse por resuelto.

Las reglas detalladas viven junto al código ([`backend/CLAUDE.md`](../backend/CLAUDE.md),
[`frontend/CLAUDE.md`](../frontend/CLAUDE.md)); este documento es el mapa. Auditoría inicial:
2026-11-09.

## Cómo se usa

- **Al cambiar código**: si el cambio toca una fila de las tablas, cumple su regla. Si la
  guarda falla, se arregla el código; no se relaja la guarda.
- **Al añadir una excepción** (una arista en `CICLOS_CONOCIDOS`, una tabla en `_ACOTADAS`, un
  `--ignore-vuln`): solo con el motivo escrito al lado. Las listas de excepciones solo
  encogen; las que tienen guarda de «ya no hace falta» fallan cuando sobra una entrada.
- **Al cerrar deuda**: se borra de la columna y, si nace una regla, se añade su guarda en el
  mismo cambio.

## Modularidad y crecimiento sin reemplazar la base

| Regla | Guarda |
| --- | --- |
| Capas de abajo arriba: `core` y `schemas` (base) → `integrations` → `modules.<dominio>` → `api`, `workers` y registros (`main`, `models`, `transiciones`). Cada capa importa solo de las de abajo. | `tests/test_arquitectura.py::test_cada_capa_solo_importa_de_las_de_abajo` |
| Los imports de la aplicación van en la cabecera del fichero, nunca dentro de una función: diferido, un nombre mal escrito no falla hasta que se ejecuta esa rama. Solo los de terceros que no siempre están instalados o pesan (`ortools`, `openpyxl`, `sentry_sdk`, `redis`) van dentro de la función que los usa. | `test_los_imports_de_la_aplicacion_van_en_la_cabecera` |
| Del resto del sistema, un dominio solo ve el `service`, los `models` y los `schemas` de otro, nunca su `router`. Su propio `router.py` es lo único del módulo que usa `app.api.deps`. | `test_un_dominio_no_usa_el_router_de_otro` y la regla anterior |
| No hay ciclos entre dominios del backend (`CICLOS_CONOCIDOS` está vacío) y ninguna dependencia nueva puede cerrar uno. Un efecto sobre otro dominio va por evento del outbox; lo que un dominio de abajo necesita del de arriba se le inyecta (`comunicaciones.conectar_entrantes`); un caso de uso que cruza dominios lo orquesta el de arriba, con sus rutas (`afiliaciones.ciclo` para la vida de la familia afiliada). | `test_ninguna_dependencia_nueva_entre_dominios_cierra_un_ciclo`, `test_los_ciclos_conocidos_que_ya_no_existen_salen_de_la_lista` |
| Panel: entre dominios solo se importa `@/features/<dominio>` (su `index.ts`); la base (`api`, `components`, `lib`, `types`) no conoce dominios, `auth` y `catalogos` no dependen de otros, `admin`, `portal` y `publico` solo los monta `App.tsx`, y no hay ciclos. | ESLint (`no-restricted-imports`) y `frontend/src/test/arquitectura.test.ts` |
| Un dominio nuevo es un directorio en `app/modules/` y otro en `src/features/`, su router en `app/api/v1/router.py` y sus modelos en `app/models.py`; no toca la base. | Las guardas de capas y de persistencia (`test_persistencia.py`) |

Cerrada el 2026-11-10 la deuda de los ciclos: en la auditoría 11 dominios formaban un solo
ciclo y no queda ninguno. Cómo se hizo, en [`deuda-ciclos-dominios.md`](deuda-ciclos-dominios.md).

## Escalabilidad

| Regla | Guarda |
| --- | --- |
| Lo que crece con el negocio se consulta por índice: toda clave foránea indexada y ningún listado ni tarea del beat recorre entera una tabla que crece. | `test_toda_llave_foranea_tiene_indice`, `test_los_caminos_calientes_no_recorren_tablas_enteras` |
| Todo listado pagina con `Page[T]` y un máximo de 200 por página. | `ParamsListado` en `app/schemas/common.py` |
| Lo pesado o lo que llama a terceros corre en el worker, nunca en un endpoint (`OR-Tools`, IA, envíos). | Revisión; `requirements-worker.txt` separa las dependencias |
| La API no guarda estado entre peticiones: sesión en base y cookies, límites en Redis cuando está desplegada; se puede escalar en horizontal. | `RateLimitMiddleware` con `ContadorRedis` fuera de local |
| Volumen proyectado a 12 meses con p95 bajo 500 ms (2 s el dashboard). | Prueba de carga (`infra/carga/`), reducida en el job del stack |

## Seguridad

| Regla | Guarda |
| --- | --- |
| Ningún endpoint abierto por omisión; las rutas públicas son una lista cerrada. La guarda recorre todas las rutas que publica el OpenAPI, no `app.routes` (FastAPI ≥ 0.137 las incluye de forma diferida). | `tests/test_permisos.py` |
| La base decide qué filas ve y escribe cada perfil (RLS) y la aplicación se conecta con un rol sin privilegios. | `test_toda_tabla_tiene_rls_y_las_politicas_de_la_matriz`, arranque que se niega con rol privilegiado |
| Ningún valor de desarrollo llega a un ambiente desplegado: claves, contraseñas, token de verificación de Meta, CORS, cookies. El administrador inicial fuera de local exige `ADMIN_PASSWORD_INICIAL`. | `test_produccion_con_valores_inseguros_no_arranca`, `test_el_seed_no_crea_el_admin_con_la_clave_de_desarrollo_fuera_de_local` |
| Ninguna vulnerabilidad publicada en lo que se despliega (dependencias de API, worker y panel). | Job **Vulnerabilidades conocidas** del CI (`pip-audit`, `npm audit --omit=dev`), del que depende el release |
| Las herramientas de desarrollo y de publicación corren en el CI con sus permisos: ninguna vulnerabilidad en las de Python y ninguna alta o crítica en las de npm (las moderadas quedan listadas en el registro del paso). | Mismo job: `pip-audit -r requirements-dev.txt` y `npm audit --audit-level=high` en el panel y en la raíz |
| Sin patrones inseguros en el código: `subprocess`, `eval`, `pickle`, SQL armado con cadenas, secretos literales. | `ruff` con las reglas `S`; cada excepción lleva `noqa` con motivo |
| La sesión no es legible por JavaScript (cookies httpOnly), ni el panel usa `fetch` o `localStorage`. | ESLint del panel, `e2e/sesion.spec.ts` |

**Deuda**: avisos moderados sin versión corregida en herramientas de desarrollo: `minimatch`
en la cadena de ESLint y el `npm` que trae `semantic-release`; se ven en el registro del job.
La auditoría corre en cada empuje, no en un horario (decidido: un aviso nuevo sin empujes se
ve en el siguiente).

## Integridad de la información

| Regla | Guarda |
| --- | --- |
| La base garantiza, Python explica: enums nativos, claves foráneas a catálogos, `CHECK`, únicos parciales, transiciones de estado por trigger, nada de negocio se borra. | `tests/test_persistencia.py`, `tests/test_migraciones.py` |
| Un efecto externo no ocurre si la transacción que lo origina se revierte (outbox). | `tests/test_outbox.py` |
| Todo evento publicado o escuchado está declarado (`declarar_evento`): un nombre mal escrito falla en el acto, no deja el efecto sin hacer. | `test_publicar_un_evento_sin_declarar_falla_en_el_acto`, `test_suscribirse_a_un_evento_sin_declarar_falla_al_importar` |
| Un evento que agota sus reintentos se registra como error (llega a Sentry) y la fila conserva su `ultimo_error`. | `test_un_evento_que_agota_los_intentos_avisa_como_error` |
| Respaldo diario restaurable, verificado en una base nueva. | Paso **Respaldo y restauración verificada** del job del stack |

## Trazabilidad

| Regla | Guarda |
| --- | --- |
| Cada alta, edición, cambio de estado y borrado de lo auditable lo registra la base, con usuario y petición, aunque se haga por SQL; la bitácora no se edita. | `test_cada_tabla_auditable_e_inmutable_tiene_su_trigger`, `tests/test_auditoria.py` |
| Cada petición lleva `X-Request-ID`, que viaja a los registros y a la auditoría. | `tests/test_base_tecnica.py` |
| Cada mensaje enviado queda trazado por destinatario con su estado de entrega. | `tests/test_comunicaciones.py` |
| Los errores de la API y de los workers llegan a Sentry cuando hay `SENTRY_DSN`. | `configurar_sentry` en API y worker |

## Interoperabilidad y capacidad de integración

| Regla | Guarda |
| --- | --- |
| API REST versionada (`/api/v1`) y descrita por OpenAPI; el panel consume los mismos tipos. | `scripts/generar_tipos_frontend.py`, `npm run typecheck` |
| Formatos estándar: fechas ISO 8601 con zona, teléfonos E.164, UUID, JSON; exportables en CSV y Excel. | `CHECK` de teléfono en la base, `tests/test_dashboard.py` |
| Cada tercero detrás de un cliente en `app/integrations/`, configurado solo por variables; ningún dominio llama a una API externa por su cuenta. | Guarda de capas (las integraciones solo usan la base) |
| Los webhooks entrantes se validan por firma, responden rápido y encolan. | `tests/test_comunicaciones.py`, `tests/test_cartera.py` |
| `eventos_declarados()` es el catálogo de lo que el sistema emite: el punto de enganche de una integración nueva. | `test_cada_dominio_declara_los_eventos_que_publica` |

**Deuda**: no hay acceso para sistemas (credenciales de servicio o claves de API) ni
webhooks salientes; la API solo admite sesiones de personas. Es lo que pedirían la página
web, las hojas de cálculo, Google Calendar o las «APIs externas» de la Sección 9. Hay una
sola pasarela de pagos (`PAYMENTS_PROVIDER` solo admite `wompi`). Ninguna integración se ha
validado contra el proveedor real desde el repositorio (`docs/backlog.md`).

## Sostenibilidad tecnológica

| Regla | Guarda |
| --- | --- |
| Dependencias con versión fija y lockfile; una transitiva que importa (seguridad, arranque) también se fija, con su motivo (`starlette`, `kombu`). | Revisión; `docker compose up --build` desde un clon limpio |
| Nada sin mantenimiento ni dependencias muertas (`python-jose` fuera; `zod` se quitó por no usarse). | Revisión; job de vulnerabilidades |
| Todo cambio llega con sus pruebas, la suite entera corre en el CI y la cobertura no baja. | Guardas de la sección *Invariante: el CI ejecuta todas las pruebas* del [`CLAUDE.md`](../CLAUDE.md) |
| El stack completo levanta con un comando desde un clon limpio. | Job **Stack con un solo comando** |
| Tecnología abierta y portable: PostgreSQL, Redis, almacenamiento compatible S3, contenedores; los datos de TIMU se exportan con `pg_dump` y los ficheros con cualquier cliente S3. | `infra/respaldos/` |
