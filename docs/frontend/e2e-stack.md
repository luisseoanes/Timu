# La e2e contra el stack (`e2e-stack/`)

Los recorridos de Playwright que corren contra el stack real, con los usuarios y los datos de
`scripts.datos_demo`, en el job «Stack con un solo comando» del CI y, antes de empujar, en local
(`E2E_BASE_URL=http://localhost:5173 npm run test:e2e:stack`). Por qué hay dos e2e y qué vigila cada
guarda está en el [`CLAUDE.md` de la raíz](../../CLAUDE.md); aquí están los límites y los datos que
condicionan cómo se escribe un recorrido. Las rutas son relativas a `frontend/`.

- **Ingresos** (login y renovación comparten un límite de 10 por minuto y por IP): la suite
  ingresa una vez por perfil (`e2e-stack/sesiones.setup.ts`, cinco perfiles), porque una que
  ingresa en cada prueba se bloquea a sí misma. Solo el perfil de equipo ingresa por el
  formulario, que gasta dos (renovación y ingreso); el resto, por la API. Con el ingreso previo
  del job suman 7: un perfil nuevo por el formulario cuesta dos. En local, dos ejecuciones
  seguidas ya lo agotan: espera un minuto.
- **Cupo de la API** (120 peticiones por minuto y por usuario): el perfil de equipo es
  `comercial@timu.co`, no el admin, porque `datos_demo` gasta el cupo del admin justo antes; por
  eso Administración se recorre con `gerencia@timu.co`, un administrador que `datos_demo` crea
  solo para los recorridos. No lances scripts propios con `comercial@timu.co` ni con
  `gerencia@timu.co` justo antes del barrido, o sus pantallas cargarán un 429: por eso
  `operacion_demo` trabaja con `admin@timu.co`, `operaciones@timu.co` y los médicos. La suite ya deja a ese perfil al borde del cupo: un
  recorrido nuevo del panel que no necesite el perfil de equipo va con el de administración
  (`sesion('admin')`), como el del Inicio.
- **Datos gruesos**: con `operacion_demo` sembrado hay muchas más filas (remisiones, rutas,
  interesados). Un recorrido busca lo que dejó `datos_demo` por su identidad (el motivo, el
  nombre), nunca el primero del listado: la primera remisión emitida, por ejemplo, puede ser una
  ya vencida. La suite pasa con los dos sembrados (así se verificó) y en el CI solo con
  `datos_demo`, porque la operación corre después.
- **Datos del día**: la ruta de prueba de la médica no siempre es de hoy (va en el primer día
  con cupo): los recorridos la buscan con `rutaDemo` (`e2e-stack/datos.ts`). Si `datos_demo` se
  sembró otro día, en local fallan con «datos_demo no dejó ninguna ruta en la próxima semana»:
  vuelve a correr `docker compose exec -T api python -m scripts.datos_demo`.

Qué deja cada script de datos y cómo ampliarlo: [datos de demostración](../datos-de-demostracion.md).
