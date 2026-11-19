# La e2e contra el stack (`e2e-stack/`)

Los recorridos de Playwright que corren contra el stack real, con los usuarios y los datos de
`scripts.datos_demo`, en el job «Stack con un solo comando» del CI y, antes de empujar, en local
(`E2E_BASE_URL=http://localhost:5173 npm run test:e2e:stack`). Por qué hay dos e2e y qué vigila cada
guarda está en el [`CLAUDE.md` de la raíz](../../CLAUDE.md); aquí están los límites y los datos que
condicionan cómo se escribe un recorrido. Las rutas son relativas a `frontend/`.

- **Un usuario por perfil** (Sección 12, [perfiles y permisos](../perfiles-y-permisos.md)): cada
  pantalla y cada recorrido van con el perfil que la usa (`atencion`, `admin`, `gerencia`,
  `comercial`, `operaciones`, `medico`, `familia` y `aliada`, en `e2e-stack/sesiones.ts`). El Inicio
  se mide con cada perfil del equipo, porque cada uno es otra pantalla.
- **Ingresos** (login y renovación comparten un límite de 10 por minuto y por IP): la suite
  ingresa una vez por perfil (`e2e-stack/sesiones.setup.ts`), porque una que ingresa en cada
  prueba se bloquea a sí misma. Solo Atención al cliente ingresa por el formulario, que gasta dos
  (renovación y ingreso); el resto, por la API: 2 + 7 = 9 de 10. Un perfil nuevo no cabe sin
  repartir los ingresos. En local, dos ejecuciones seguidas ya lo agotan: espera un minuto.
- **Cupo de la API** (120 peticiones por minuto y por usuario): repartido entre los perfiles, ninguno
  va al borde. `datos_demo` y `operacion_demo` hablan con la API con los mismos usuarios (cada ruta
  con el perfil que la admite), así que el barrido justo después puede recibir algún 429: espera a
  `Retry-After` y vuelve a cargar.
- **Datos gruesos**: con `operacion_demo` sembrado hay muchas más filas (remisiones, rutas,
  interesados). Un recorrido busca lo que dejó `datos_demo` por su identidad (el motivo, el
  nombre), nunca el primero del listado: la primera remisión emitida, por ejemplo, puede ser una
  ya vencida. La suite pasa con los dos sembrados (así se verificó) y en el CI solo con
  `datos_demo`, porque la operación corre después.
- **Lo que la prueba crea a propósito**: el barrido emite un carnet (con `atencion@timu.co`, de la
  mascota de `datos_demo` con un preventivo aplicado) para medir la verificación pública con sus
  tablas; emitir es lo que hace el equipo desde el panel. La encuesta no se puede abrir con un
  token real (solo está en la base): se mide con uno inexistente, y su formulario en `e2e/`.
- **Datos del día**: la ruta de prueba de la médica no siempre es de hoy (va en el primer día
  con cupo): los recorridos la buscan con `rutaDemo` (`e2e-stack/datos.ts`). Si `datos_demo` se
  sembró otro día, en local fallan con «datos_demo no dejó ninguna ruta en la próxima semana»:
  vuelve a correr `docker compose exec -T api python -m scripts.datos_demo`.

Qué deja cada script de datos y cómo ampliarlo: [datos de demostración](../datos-de-demostracion.md).
