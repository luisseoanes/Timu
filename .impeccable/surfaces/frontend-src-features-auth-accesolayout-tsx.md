---
version: 1
slug: "frontend-src-features-auth-accesolayout-tsx"
primary_target: "frontend/src/features/auth/AccesoLayout.tsx"
related_targets: ["frontend/src/features/auth/LoginPage.tsx","frontend/src/features/auth/RecuperarPage.tsx"]
---

# Páginas públicas · Acceso (R3-PUB-01)

## Alcance y modo

Ingreso, recuperación, restablecimiento y activación de la cuenta: las cuatro pantallas de
`AccesoLayout`. Superficie dentro de la línea visual de Familias (`DESIGN.md`), sin sorteo: la
composición la eligió el usuario. Modo: Operate (la tarea es entrar), con el panel de marca como el
único sitio donde la marca se presenta. Construcción: en código.

## Público, tarea y restricciones

- El equipo y la clínica aliada entran con correo y contraseña, a diario y en escritorio; el médico,
  también desde el celular. Las familias llegan desde un enlace de WhatsApp o del correo, casi
  siempre en el celular: entran con un código por WhatsApp o con la contraseña de su cuenta, o
  abren el enlace para activarla o restablecerla.
- Restricciones: roles de color del manual (sobre marino solo blanco, marino-200, verde-500 y
  naranja-500, regla 6), una sola acción verde por vista, controles de 44 px en táctil, WCAG 2.2
  AA, Radix para lo interactivo. El panel no adivina el estado de un enlace: lo dice la API.

## Direction contract

THESIS: Entrar a TIMU es subirse a la línea: a la izquierda, sobre marino, el logo en blanco, una
frase y la línea de metro de una familia dibujada como señalética; a la derecha, el formulario y
nada más. Cada pantalla le habla a quien llega (la activación, a la familia). Rechaza el
antetítulo en pastilla, la tarjeta de vidrio con sombra, las tres funciones con icono que venden la
plataforma al equipo y el enlace que solo dice que no vale después de escribir dos veces la clave.

OWN-WORLD: El de `DESIGN.md`. Panel marino plano (`superficie-marca`), GeosansLight a 34 px en
blanco, la línea de 8 px en verde-500 con estaciones de 24 px: hechas llenas, la de hoy con anillo
blanco y halo verde, las que faltan en contorno marino-200 sobre un tramo translúcido. Formulario
sobre blanco: campos de 40 px (44 en táctil), selector segmentado, un verde lleno.

STORY: Ana abre el enlace de activación que le llegó por WhatsApp; la pantalla la saluda por su
nombre, le pide la contraseña una vez con su confirmación y, al guardarla, la deja dentro de su
portal. Si el enlace venció, lo dice de entrada y le ofrece pedir otro.

FIRST VIEWPORT: 1440×900: dos columnas, el panel marino a la izquierda (logo completo arriba, la
frase y la línea a media altura, la nota de datos protegidos abajo) y el formulario centrado en una
columna de 400 px a la derecha, con el título a 34 px y el verde a todo el ancho. 390×844: una
franja marina arriba con el logo en blanco y la línea en miniatura, y el formulario debajo, con el
verde dentro de la primera pantalla.

FORM: dos columnas con panel de marca, heredadas del ingreso anterior y rehechas en la línea;
seed: none (pinned) — el usuario eligió «Marino con la línea» («Sin sorteo. Dos columnas desde 900
px: panel marino plano con el logo completo en blanco, un mensaje que cambia según la pantalla (en
/activar le habla a la familia) y la línea de metro dibujada como gesto de marca, en lugar de la
tarjeta de vidrio y la pastilla. Por debajo de 900 px, una franja marina arriba con el logo en
blanco y el formulario debajo. Cumple el criterio de la fila (“el panel de marca pasa a
marino”)»), el 2026-11-15.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Decisiones tomadas (2026-11-15)

- **El ingreso se elige por público, con la contraseña dentro de Familias** (decidido con el
  usuario: «Se mantiene “Equipo TIMU” / “Familias”; Familias ofrece el código y, debajo,
  “Ingresar con contraseña”. La clínica aliada sigue entrando por “Equipo TIMU”»). Si se llega
  desde una ruta del portal, el selector abre en Familias.
- **La API comprueba el enlace al abrirlo** (`POST /auth/enlace`, con el token en el cuerpo y no
  en la URL, que el registro de accesos escribe entera): vigente, usado, vencido o inválido, su
  propósito y el nombre de pila, sin gastarlo y con el límite estricto de las rutas de
  credenciales. La pantalla saluda o dice de entrada que el enlace no sirve y ofrece otro.
- **Al activar o restablecer se entra directo**: `POST /auth/restablecer` abre la sesión como el
  ingreso y la pantalla lleva a cada uno a su espacio.

## Pendiente

- Lo que quede, en la hoja de ruta («Lo que quedó del acceso»).
