# Trampas conocidas del panel

Lo que ya costó tiempo en las pruebas, los estilos y las herramientas del panel, una línea cada
una. Las reglas están en el [`CLAUDE.md` del frontend](../../frontend/CLAUDE.md), que repite las
que más se tropiezan; las de la e2e contra el stack, en [e2e-stack.md](e2e-stack.md). Las rutas
son relativas a `frontend/`. Una trampa nueva se añade aquí.

- La ficha vacía y la abierta de un listado con ficha comparten `aria-label` («Ruta abierta»): espera a un elemento de la ficha (su título), no a la región, o la prueba lee el marcador.
- Si una prueba falla con «peticiones sin handler» que no son suyas, eran de la anterior: `setup.ts`
  ya espera la red al cerrar cada prueba (tope de 2 s); una consulta que se dispara más tarde (un
  temporizador, un `refetchInterval`) se simula en la prueba que la provoca.
- Con una ventana de Radix abierta, el resto de la página queda oculto a los lectores de pantalla y `findByRole` no lo encuentra hasta que se cierra. Crear y abrir la ficha encadena el cierre, el listado y la ficha: espera a su título con `{ timeout: 5000 }`. Con un segundo falla a veces con la suite entera bajo cobertura.
- `Pestanas` sin `valor` no cambia de pestaña al cambiar la URL: un enlace desde otra pestaña que abre un registro (`?interesado=`) lo deja en una pestaña oculta. La página controla la pestaña y vuelve a la del registro cuando este cambia (`ComercialPage.tsx`, `ClinicaPage.tsx`). Remontarla con un `key` no sirve: al cerrar la ficha cambia la `key` y vuelve a la primera.
- Dentro de `.fila-cuerpo` cada `span` es un bloque: un dato en un `span` propio («60 min», un número) parte la línea. Escríbelo en un solo texto.
- `npx eslint`, `npx tsc` o `npx vitest` desde la raíz del repositorio descargan otra versión y fallan: se corren desde `frontend/`.
- Con la máquina cargada (`uptime` alto), `verificar` agota los tiempos de Vitest: corre los mismos
  pasos por separado, con `npx vitest run --coverage --maxWorkers=2`, antes de dar por buena una falla.
- `playwright test -g` compara con el título unido por espacios, no por «›»: la ruta `admin` del barrido es `-g "admin admin$"`.
- **MSW usa el primer handler que coincide**: en `server.use(...base, override)` gana `base`. Los comunes van en un `beforeEach` y cada prueba los sustituye con su propio `server.use`.
- En jsdom el parser multipart de undici no acepta el `File` de jsdom, y el nombre llega como `blob`: una subida se comprueba leyendo `await request.text()`, no con `request.formData()`.
- Al simular `window.location` con `vi.stubGlobal`, dale el `pathname` de una página pública: si no, el cliente manda a `/login` ante el 401 de `/auth/me` (`PAGINAS_PUBLICAS` en `src/api/client.ts`).
- El proyecto no usa Prettier: no corras `npx prettier`, que descarga uno y reformatea el fichero entero. El formato lo revisa ESLint.
- Vite incrusta como `data:` los recursos de menos de 4 KB: compara el `src` con el import del fichero, no con su nombre.
- Con una ventana de Radix abierta, el `body` lleva `pointer-events: none` y `elementFromPoint` se lo salta: quítalo mientras mides qué hay pintado encima.
- Una regla con `display:` le gana al atributo `hidden`, y jsdom no aplica el CSS: un pliegue que
  no pliega pasa en Vitest. Se prueba en Playwright (`e2e/`) con `toBeHidden()`.
- `moneda()` separa con espacio duro (`$ 225.000`), y lo mismo cualquier `\u00a0` (el «40 %»
  que da la API): Testing Library lo normaliza a espacio, así que búscalo con `\s` en la expresión.
  Si el nombre accesible de un título no casa, compara su `toHaveTextContent`.
- En `e2e/`, `page.route` da prioridad al último registrado: el comodín (`**/api/v1/**`) primero
  y las rutas de la prueba después.
- Un handler de MSW que ignora los parámetros contesta igual a dos consultas de la misma ruta: si
  la pantalla pide dos veces `/servicios` (agenda y `abiertos=true`), las filas salen duplicadas.
- Para congelar la hora sin romper MSW ni userEvent: `vi.useFakeTimers({ toFake: ['Date'] })` y
  `vi.useRealTimers()` en un `finally`.
- `useNombreTipoServicio` devuelve el código («consulta domiciliaria») hasta que llega el
  catálogo: un nombre que lo incluye se busca con `findBy`, no con `getBy`.
- `npm run test:e2e` sirve `dist/` con `vite preview` (y en local reutiliza el que ya esté arriba):
  no recompila. Tras cambiar el panel, `npx vite build` antes, o la prueba mira la versión vieja.
- Para enfocar un campo al abrir un `Modal`, `autoFocus` en el campo: Radix respeta el foco que ya
  está dentro (`SelectorFamilia`, prop `enfocar`).
- `:is()` no admite pseudoelementos (`:is(.a::after, .b)` invalida la regla entera): sepáralos con coma.
- jsdom no desplaza: para probar un manejador de `scroll`, `Object.defineProperty(el, 'scrollTop',
  { value, configurable: true })` y `fireEvent.scroll(el)`.
- Una animación de CSS se prueba en `e2e/` leyendo `getComputedStyle(el, '::before').animationName`;
  con `test.use({ reducedMotion: 'reduce' })` da `none` (la apaga `base.css`).
- `margin-inline: auto` en un hijo de grid o flex lo encoge a su contenido: dale también
  `width: min(<máx>, 100%)`.
- `verificar` muestra un aviso previo de ESLint en `AuthContext.tsx`
  (`react-refresh/only-export-components`): no es de tu cambio.
- Una ayuda dentro del `<label>` entra en el nombre accesible del campo («Valor de la atención Lo que…») y
  `getByLabelText` no lo encuentra: el campo con ayuda va en `div.campo` con `<label htmlFor>`.
- El `onSuccess` que se pasa a `mutate(datos, { onSuccess })` no se ejecuta si el componente que
  llamó se desmonta antes (al reportar una remisión, el formulario desaparece porque la remisión
  pasa a «Atendida»). Lo que tiene que pasar sí o sí va en el `onSuccess` del propio `useMutation`
  (`useReportarAtencion(codigo, alReportar)`). En Vitest puede pasar por los tiempos y fallar en el
  navegador.
- Un bloque nuevo de `vistas.css` insertado antes de `.filtros` o `.listado .filtros > .input`
  pierde contra ellos: sube la especificidad (`.listado .filtros.mi-clase`) o ponlo detrás. Igual un
  `@container` o `@media` escrito antes de la regla base del mismo selector: con la misma
  especificidad, gana la que va después.
- `role="status"` en o dentro de un `h1` deja el encabezado sin nombre accesible en Chromium; jsdom
  sí lo calcula, así que Vitest pasa y Playwright no lo encuentra.
- `.tabla-apilable` usa `td::before` para la etiqueta y apila bajo 640 px de contenedor, también en
  una ficha estrecha de escritorio: una tabla que debe seguir en columnas lleva su propio corte
  (`.registro-comparador`).
- Exportar funciones o constantes desde un `.tsx` de componentes dispara
  `react-refresh/only-export-components`: van a un `.ts` del dominio (`registro.ts`, `admin/planes.ts`).
- `e2e/` no lo revisa `tsc`: sus datos simulados de la API se quedan atrás sin aviso (el comparador
  se cayó por un plan sin `adicionales`). Al cambiar un schema, revísalos a mano.
- Una página pública nueva va en `PAGINAS_PUBLICAS` (`src/api/client.ts`): si no, un 401 la manda
  a `/login`. La portada (`/`) se compara entera, no como prefijo.
- La guarda de tokens toma por color un nombre de variable con una palabra de color en inglés
  (`--linea-red` falló): nómbralas en español.
- Dos Playwright a la vez se pisan: cada uno vacía `test-results/` al empezar y el otro falla con
  `ENOENT … .trace`. `test:e2e` y `test:e2e:stack`, uno detrás de otro.
- Si el hook de diseño no devuelve nada (ni siquiera «No deterministic…»), pasa el detector a mano:
  `.claude/skills/impeccable/scripts/impeccable detect --json <fichero>`.
