# Manual de marca de TIMU

Este documento tiene dos partes:

- **Parte I. Manual de TIMU.** Es la transcripción del manual de marca que entregó TIMU (PDF
  de 8 páginas: esencia, color, logo, planes, tipografía, voz y tokens). No se edita: si TIMU
  publica otra versión, se vuelve a transcribir.
- **Parte II. Ampliación para la plataforma.** Son los colores, roles y reglas que el manual no
  trae y que la plataforma necesita para texto, estados, foco, gráficos y accesibilidad. Se
  validó el 2026-11-10 y reemplaza por completo la paleta anterior en tonos menta.

Aplica a todo lo que TIMU dice y muestra desde la plataforma: el panel del equipo, el portal de
familias, el espacio de la clínica aliada, las páginas públicas, los mensajes de WhatsApp y
los correos.

En el código vive en [`frontend/src/styles/tokens.css`](../frontend/src/styles/tokens.css).
El sistema de interfaz (escala tipográfica, espaciado, componentes) se documenta aparte, en
`DESIGN.md`. El contexto de producto está en [`PRODUCT.md`](../PRODUCT.md). Lo que falta de
TIMU está en [pendientes externos](pendientes-externos.md#marca-e-identidad-manual-de-marca).

---

# Parte I. Manual de TIMU

## 1. Esencia

### Quiénes somos

TIMU es medicina veterinaria prepagada para perros y gatos. Facilita el acceso a la atención
veterinaria y ayuda a las familias a gestionar su costo, con servicios propios (clínica y
domicilio) y una red de prestadores aliados.

| Cercanos | Precisos | Presentes |
| --- | --- | --- |
| Hablamos con tutores que ven a su peludito como familia. Nada de jerga sin explicar. | En salud, urgencias y condiciones del plan, decimos las cosas claras y completas. | Triage por chat 24/7 y atención en casa, en clínica TIMU o con un aliado. Acompañamos más allá de la urgencia. |

## 2. Color

### Paleta

Los cuatro colores del logo: verde, naranja, azul y marino.

| Color | Dónde está en el logo | Hex | RGB |
| --- | --- | --- | --- |
| Verde TIMU | Letras T y U | `#98B833` | 152, 184, 51 |
| Naranja TIMU | M, mitad izquierda | `#D48200` | 212, 130, 0 |
| Azul TIMU | M, mitad derecha | `#477095` | 71, 112, 149 |
| Marino TIMU | Texto y siluetas | `#111537` | 17, 21, 55 |

Son los colores con que la diseñadora exporta el logo para pantalla (las láminas PNG del
manual original). El naranja se ajustó el 2026-11-11 a ese valor: antes era `#D68A11`,
medido sobre una imagen del logo. El logo en vector (`Marca TIMU.ai`) guarda los mismos
números en Adobe RGB; convertidos con gestión de color saldrían más saturados, pero las
exportaciones de la diseñadora no lo hacen, y la plataforma sigue a las exportaciones. El texto del manual original de 2021 da otros valores (un azul petróleo y un
naranja claro) que no usa ni su logo ni ninguna pieza; TIMU confirmó que valen los del logo.

### Escalas

Cada color con cinco tintes, del más intenso al más claro:

| Color | Base | Tinte 1 | Tinte 2 | Tinte 3 | Tinte 4 | Tinte 5 |
| --- | --- | --- | --- | --- | --- | --- |
| Verde | `#98B833` | `#ADC65C` | `#C1D485` | `#D6E3AD` | `#E5EDCC` | `#F3F6E7` |
| Naranja | `#D48200` | `#DD9B33` | `#E5B466` | `#EECD99` | `#F4E0BF` | `#FAF0E0` |
| Azul | `#477095` | `#6C8DAA` | `#91A9BF` | `#B5C6D5` | `#D1DBE4` | `#E9EEF2` |
| Marino | `#111537` | `#41445F` | `#707387` | `#A0A1AF` | `#C4C4CD` | `#E2E3E7` |

### Combinaciones legibles

Contraste según WCAG: el texto normal necesita 4.5 o más. Verde y naranja sobre blanco no
alcanzan para texto: se usan como fondo con texto marino.

| Texto | Fondo | Contraste | Nivel |
| --- | --- | --- | --- |
| Marino | Blanco | 17.7:1 | AAA |
| Marino | Verde | 7.8:1 | AAA |
| Marino | Naranja | 6.3:1 | AA |
| Blanco | Azul | 5.2:1 | AA |
| Blanco | Marino | 17.7:1 | AAA |
| Verde | Marino | 7.8:1 | AAA |

Las seis cifras se comprobaron con la fórmula de WCAG 2.2 y coinciden con el manual.

## 3. Logo

La T y la U en verde, la M partida en naranja y azul, y el texto y las siluetas en marino. **El
logo no se modifica ni se recolorea.**

- Verde: letras T y U.
- Naranja: mitad izquierda de la M.
- Azul: mitad derecha de la M.
- Marino: «Medicina veterinaria prepagada» y siluetas.

## 4. Un color por plan

Sugerencia de uso: cada plan toma un color del logo para reconocerlo de un vistazo en piezas y
chat.

| Plan | Color | Precio en el manual | Descripción |
| --- | --- | --- | --- |
| Colita Feliz | Naranja | $35.500/mes | La puerta de entrada. |
| Mi Amigo Fiel | Verde | $69.000/mes | El plan principal. |
| Amigos por Siempre | Azul | $98.000/mes | La mayor cobertura. |

El manual dice que son los precios mensuales según timu.com.co y que aplican los términos y
condiciones de cada plan. La propia web publica otros precios en `/planes/` (ver pendientes
externos). Por eso **la plataforma nunca copia precios de este documento**: los toma del
catálogo de planes de la API.

## 5. Tipografía

Una sola familia geométrica y ligera, en versión recta y oblicua.

| Fuente | Uso |
| --- | --- |
| GeosansLight | Títulos, texto corrido y botones |
| GeosansLight-oblique | Énfasis, notas y condiciones del plan |

| Nivel | Fuente | Tamaño | Ejemplo |
| --- | --- | --- | --- |
| Título 1 | GeosansLight | 30 pt | Tu peludito, bien cuidado |
| Título 2 | GeosansLight | 20 pt | Orientación por chat 24/7 |
| Título 3 | GeosansLight | 14 pt | Vacunas y desparasitación al día |
| Texto | GeosansLight | 11,5 pt | Te recordamos cada vacuna y desparasitación, y te guiamos para decidir si tu peludito necesita una consulta o una atención presencial. |
| Nota legal | GeosansLight-oblique | 9 pt | Los planes excluyen preexistencias, los beneficios no se acumulan y los topes aplican por episodio. |

El PDF usa Inter Light como sustituta de vista previa porque el archivo de GeosansLight no se
adjuntó.

## 6. Voz

Una sola marca con dos registros. Cambiamos de tono según lo que está en juego.

| Registro | Cuándo | Ejemplo |
| --- | --- | --- |
| Cercano y juguetón | Redes sociales, recordatorios, bienvenida | ¡Hoy toca desparasitación! Te dejamos el recordatorio por WhatsApp para que no cargues con todo tú solo. |
| Experto y preciso | Salud, urgencias, condiciones del plan | Si tu peludito tiene dificultad para respirar o vómito persistente, es una urgencia: te derivamos a atención presencial de inmediato. |

| Sí decimos | No decimos |
| --- | --- |
| «Plan de salud prepagado» y «medicina veterinaria prepagada» | «Seguro para mascotas» |
| «Peludito», «peludo» y «la manada TIMU» | «Cubrimos todo», «ilimitado», «sin costo» |
| Descuentos con su porcentaje y su tope por episodio | Términos médicos sin explicar |
| Exclusiones y carencias, de frente | |

## 7. Colores en código

Tokens que trae el manual para diseño y desarrollo web:

```css
:root {
  --timu-verde:   #98B833;  /* letras T y U */
  --timu-naranja: #D48200;  /* M, mitad izquierda */
  --timu-azul:    #477095;  /* M, mitad derecha */
  --timu-marino:  #111537;  /* texto y siluetas */
  --timu-blanco:  #FFFFFF;

  --font-base: 'GeosansLight', sans-serif;
  /* énfasis: GeosansLight-oblique */
}
```

En la plataforma estos valores son los pasos `500` de verde, naranja y azul y el `900` de marino
(ver la Parte II). Los nombres `--timu-*` no se usan en el código.

---

# Parte II. Ampliación para la plataforma

## 8. Lo que el manual no resuelve

El manual define la identidad, pero una aplicación necesita más:

- **Tonos oscuros.** Sobre blanco, el verde da 2.27:1 y el naranja 3.00:1: no sirven para texto
  (4.5) ni para un gráfico con significado (3.0). Las escalas del manual solo aclaran, así que
  sin tonos oscuros no hay texto de marca, ni estado al pasar el cursor, ni texto legible sobre
  los tintes.
- **Rojo.** La marca no tiene, y la plataforma necesita «peligro», «vencido» y «cancelar».
- **Neutros de interfaz.** Faltan un lienzo de aplicación, un borde de control con 3:1 (WCAG
  1.4.11) y un texto secundario que pase 4.5 también sobre el lienzo y los tintes.
- **Foco de teclado**, sobre claro y sobre oscuro.
- **Series de gráfico** con 3:1 sobre blanco.

## 9. Paleta completa

Los pasos del manual se respetan tal cual. Los derivados conservan el matiz del color en OKLCH
y solo bajan la luminosidad hasta el contraste que exige su función. Cada contraste se mide
contra blanco (`#FFFFFF`) y contra el lienzo (`#F5F6F1`).

### Verde

| Paso | Hex | Origen | vs blanco | vs lienzo | Para qué |
| --- | --- | --- | --- | --- | --- |
| 50 | `#F3F6E7` | manual | 1.10 | 1.01 | Selección, botón suave, estado correcto |
| 100 | `#E5EDCC` | manual | 1.21 | 1.12 | Botón suave al pasar el cursor |
| 200 | `#D6E3AD` | manual | 1.36 | 1.25 | Bordes de elementos seleccionados |
| 300 | `#C1D485` | manual | 1.61 | 1.48 | Ilustración |
| 400 | `#ADC65C` | manual | 1.91 | 1.76 | Ilustración |
| **500** | `#98B833` | **manual · logo** | 2.27 | 2.09 | Fondo de la acción principal, con texto marino |
| 600 | `#769116` | derivado | 3.60 | 3.32 | Indicador de seleccionado, serie de gráfico, acción al pasar el cursor |
| 700 | `#587000` | derivado | 5.63 | 5.18 | Texto verde sobre claro |
| 800 | `#415800` | derivado | 8.01 | 7.38 | Texto del estado correcto y del botón suave |
| 900 | `#2E4200` | derivado | 11.08 | 10.20 | Reserva |

### Naranja

| Paso | Hex | Origen | vs blanco | vs lienzo | Para qué |
| --- | --- | --- | --- | --- | --- |
| 50 | `#FAF0E0` | derivado | 1.13 | 1.04 | Fondo del estado de alerta |
| 100 | `#F4E0BF` | derivado | 1.29 | 1.19 | |
| 200 | `#EECD99` | derivado | 1.52 | 1.40 | |
| 300 | `#E5B466` | derivado | 1.90 | 1.75 | Ilustración |
| 400 | `#DD9B33` | derivado | 2.38 | 2.19 | Ilustración |
| **500** | `#D48200` | **logo** | 3.00 | 2.77 | Color del plan Colita Feliz, con texto marino |
| 600 | `#BE7700` | derivado | 3.60 | 3.32 | Serie de gráfico |
| 700 | `#9B5600` | derivado | 5.64 | 5.19 | Texto naranja sobre claro |
| 800 | `#813E00` | derivado | 8.01 | 7.37 | Texto del estado de alerta |

### Azul

| Paso | Hex | Origen | vs blanco | vs lienzo | Para qué |
| --- | --- | --- | --- | --- | --- |
| 50 | `#E9EEF2` | manual | 1.17 | 1.08 | Fondo del estado de información |
| 100 | `#D1DBE4` | manual | 1.40 | 1.29 | |
| 200 | `#B5C6D5` | manual | 1.75 | 1.61 | |
| 300 | `#91A9BF` | manual | 2.43 | 2.24 | Ilustración |
| 400 | `#6C8DAA` | manual | 3.48 | 3.21 | Ilustración |
| **500** | `#477095` | **manual · logo** | 5.22 | 4.81 | Enlaces, foco, serie de gráfico, plan Amigos por Siempre con texto blanco |
| 600 | `#396186` | derivado | 6.51 | 5.99 | Reserva |
| 700 | `#274F73` | derivado | 8.56 | 7.88 | Enlace al pasar el cursor, texto del estado de información |
| 800 | `#153E60` | derivado | 11.11 | 10.23 | Reserva |

### Marino (neutros)

Los grises de la plataforma salen del marino, no de un gris puro, para que convivan con la
marca.

| Paso | Hex | Origen | vs blanco | vs lienzo | Para qué |
| --- | --- | --- | --- | --- | --- |
| 100 | `#E2E3E7` | manual | 1.28 | 1.18 | Bordes decorativos y separadores, fondo del estado neutro |
| 200 | `#C4C4CD` | manual | 1.73 | 1.59 | Texto secundario sobre marino |
| 300 | `#A0A1AF` | manual | 2.56 | 2.35 | Texto deshabilitado (WCAG lo exime) |
| 400 | `#85889D` | derivado | 3.50 | 3.22 | Borde de campos, casillas y controles |
| 500 | `#707387` | manual | 4.68 | 4.31 | Borde de controles al pasar el cursor. No sirve para texto sobre el lienzo |
| 600 | `#5F6275` | derivado | 6.02 | 5.54 | Texto secundario, etiquetas, iconos inactivos |
| 700 | `#41445F` | manual | 9.47 | 8.72 | Texto de cuerpo, texto del estado neutro |
| 800 | `#282E53` | derivado | 13.08 | 12.04 | Superficie de marca al pasar el cursor |
| **900** | `#111537` | **manual · logo** | 17.70 | 16.30 | Títulos, texto de la acción principal, superficie de marca |

### Lienzo y blanco

| Nombre | Hex | Origen | Para qué |
| --- | --- | --- | --- |
| Lienzo | `#F5F6F1` | derivado | Fondo general de la aplicación y zonas hundidas. Un blanco roto con un leve sesgo verde, entre el blanco y el tinte más claro del verde. |
| Blanco | `#FFFFFF` | manual | Tarjetas, barra lateral, campos y ventanas |

### Rojo (auxiliar)

No es un color de marca: solo comunica peligro, error o una acción destructiva, y nunca decora.
Su matiz es cálido, para que no se confunda con el naranja.

| Paso | Hex | Origen | vs blanco | vs lienzo | Para qué |
| --- | --- | --- | --- | --- | --- |
| 50 | `#FFF2EF` | derivado | 1.09 | 1.01 | Fondo del estado de peligro |
| 100 | `#FFD9CE` | derivado | 1.31 | 1.20 | Borde de un aviso de error |
| 500 | `#C0392B` | derivado | 5.44 | 5.01 | Fondo de la acción destructiva, con texto blanco |
| 700 | `#A92115` | derivado | 7.20 | 6.63 | Texto de error, acción destructiva al pasar el cursor |
| 800 | `#892319` | derivado | 9.06 | 8.34 | Texto del estado de peligro |

## 10. Roles

Los componentes y las vistas nunca nombran un color de la paleta: usan un **rol**, que dice para
qué sirve el color y apunta a un paso de la paleta. Cambiar el aspecto de algo es cambiar a qué
paso apunta su rol, en un solo sitio.

Mínimos de WCAG 2.2: **4.5:1** para texto (1.4.3) y **3:1** para bordes de control, indicadores
de estado, foco y gráficos (1.4.11 y 2.4.13). Los contrastes de la tabla se midieron sobre el
fondo indicado.

### Texto

| Rol | Paso | Sobre | Contraste | Mínimo |
| --- | --- | --- | --- | --- |
| `--texto-titulo` | marino-900 | blanco / lienzo | 17.70 / 16.30 | 4.5 |
| `--texto` | marino-700 | blanco / lienzo | 9.47 / 8.72 | 4.5 |
| `--texto-suave` | marino-600 | blanco / lienzo | 6.02 / 5.54 | 4.5 |
| `--texto-suave` | marino-600 | tintes 50 de verde, naranja, azul y rojo; marino-100 | 5.15 a 5.50; 4.69 | 4.5 |
| `--texto-deshabilitado` | marino-300 | blanco | 2.56 | exento |
| `--texto-enlace` | azul-500 | blanco / lienzo | 5.22 / 4.81 | 4.5 |
| `--texto-enlace-hover` | azul-700 | blanco / lienzo | 8.56 / 7.88 | 4.5 |
| `--texto-error` | rojo-700 | blanco / lienzo | 7.20 / 6.63 | 4.5 |
| `--texto-sobre-marca` | blanco | marino-900 | 17.70 | 4.5 |
| `--texto-sobre-marca-suave` | marino-200 | marino-900 | 10.22 | 4.5 |
| `--texto-sobre-marca-acento` | verde-500 | marino-900 | 7.79 | 4.5 |

### Superficies y bordes

| Rol | Paso | Contraste | Mínimo |
| --- | --- | --- | --- |
| `--superficie-lienzo` | lienzo | — | — |
| `--superficie` | blanco | — | — |
| `--superficie-hundida` | lienzo | — | — |
| `--superficie-seleccion` | verde-50 | — | — |
| `--superficie-marca` | marino-900 | — | — |
| `--superficie-marca-hover` | marino-800 | blanco encima: 13.08 | 4.5 |
| `--borde` | marino-100 | 1.28 sobre blanco | decorativo, sin mínimo |
| `--borde-control` | marino-400 | 3.50 sobre blanco / 3.22 sobre lienzo | 3 |
| `--borde-control-hover` | marino-500 | 4.68 sobre blanco / 4.31 sobre lienzo | 3 |
| `--superficie-sobre-marca` | blanco al 8 % sobre marino-900 | blanco encima: 14.29 | 4.5 |
| `--borde-sobre-marca` | blanco al 22 % | — | decorativo, sin mínimo |
| `--pista` | marino-100 | — | decorativa: pista de barras y anillos |
| `--velo` | marino-900 al 50 % | — | — |

### Acciones

| Rol | Fondo | Texto | Contraste | Mínimo |
| --- | --- | --- | --- | --- |
| Principal: `--accion-fondo` / `--accion-texto` | verde-500 | marino-900 | 7.79 | 4.5 |
| Principal al pasar el cursor: `--accion-fondo-hover` | verde-600 | marino-900 | 4.92 | 4.5 |
| Suave: `--accion-suave-fondo` / `--accion-suave-texto` | verde-50 | verde-800 | 7.31 | 4.5 |
| Suave al pasar el cursor: `--accion-suave-fondo-hover` | verde-100 | verde-800 | 6.61 | 4.5 |
| Secundaria | blanco con `--borde-control` | marino-900 | 17.70 | 4.5 |
| Destructiva: `--peligro-accion-fondo` / `--peligro-accion-texto` | rojo-500 | blanco | 5.44 | 4.5 |
| Destructiva al pasar el cursor: `--peligro-accion-fondo-hover` | rojo-700 | blanco | 7.20 | 4.5 |
| Sobre superficie de marca | verde-500 | marino-900 | 7.79 | 4.5 |

### Selección y foco

| Rol | Paso | Sobre | Contraste | Mínimo |
| --- | --- | --- | --- | --- |
| `--indicador-seleccion` | verde-600 | blanco / lienzo | 3.60 / 3.32 | 3 |
| `--foco` | azul-500 | blanco / lienzo | 5.22 / 4.81 | 3 |
| `--foco-sobre-marca` | verde-500 | marino-900 | 7.79 | 3 |

### Estados

Cada estado es un par fondo + texto, y siempre lleva texto e icono además del color (WCAG
1.4.1). Su texto llega a 7:1 o más porque los distintivos usan letra pequeña.

| Estado | Ejemplos | Fondo | Texto | Contraste |
| --- | --- | --- | --- | --- |
| Correcto (`--estado-ok-*`) | Afiliación activa, cuota al día, preventivo aplicado | verde-50 | verde-800 | 7.31 |
| Alerta (`--estado-alerta-*`) | Mora temprana, preventivo por vencer | naranja-50 | naranja-800 | 7.09 |
| Información (`--estado-info-*`) | Prospecto, servicio programado | azul-50 | azul-700 | 7.33 |
| Peligro (`--estado-peligro-*`) | Cancelada, preventivo vencido, error | rojo-50 | rojo-800 | 8.28 |
| Neutro (`--estado-neutro-*`) | Congelada, sin datos, borrador | marino-100 | marino-700 | 7.39 |

### Planes

| Rol | Paso | Texto encima | Contraste |
| --- | --- | --- | --- |
| `--plan-naranja` / `--plan-naranja-texto` | naranja-500 | marino-900 | 5.89 |
| `--plan-verde` / `--plan-verde-texto` | verde-500 | marino-900 | 7.79 |
| `--plan-azul` / `--plan-azul-texto` | azul-500 | blanco | 5.22 |

Los roles se nombran por color, no por plan: cada plan del catálogo declara su color (`naranja`,
`verde` o `azul`) y la interfaz toma el rol de ese color. Hoy son Colita Feliz, Mi Amigo Fiel y
Amigos por Siempre, en ese orden (sección 4).

### Gráficos

Las series se usan siempre en este orden, y todas llegan a 3:1 sobre blanco. El rojo no se usa
como serie, para que no se lea como alarma.

| Rol | Paso | vs blanco | vs lienzo |
| --- | --- | --- | --- |
| `--serie-1` | verde-600 | 3.60 | 3.32 |
| `--serie-2` | naranja-600 | 3.60 | 3.32 |
| `--serie-3` | azul-500 | 5.22 | 4.81 |
| `--serie-4` | marino-900 | 17.70 | 16.30 |

## 11. Reglas de uso del color

1. **Verde y naranja de marca nunca como texto ni como única señal sobre fondo claro.** Para eso
   están sus pasos 600 (gráficos e indicadores) y 700 u 800 (texto).
2. **Un solo botón principal por vista.** El verde lleno es la acción más importante de la
   pantalla. El resto de acciones son secundarias o suaves.
3. **Cada color tiene su papel.** El verde es la acción y la selección; el azul, la navegación,
   el foco y la información; el naranja, la alerta y el plan Colita Feliz; el rojo, solo el
   peligro; el marino, el texto y la superficie de marca.
4. **El plan y el estado no se confunden.** Los colores de los planes coinciden con los de
   alerta, correcto e información, así que se distinguen por la forma:
   - el **plan** es identidad: un cuadrado del color del plan y el nombre en marino; a todo
     color, solo donde el plan es protagonista (elegir plan, cabecera del portal);
   - el **estado** es una pastilla con fondo tintado, texto oscuro e icono.
5. **El color de un plan sale del catálogo, no de su nombre.** La interfaz no deduce el color
   comparando nombres de plan.
6. **Sobre la superficie de marca (marino)** solo van blanco, marino-200, verde-500 y
   naranja-500. El azul da 3.39:1 sobre marino: sirve para un gráfico, no para texto.
7. **Ningún texto sobre un degradado o una imagen** sin comprobar su contraste en el punto más
   desfavorable.
8. **Las sombras y el velo de las ventanas salen del marino**, no del negro.

## 12. Tipografía en la plataforma

- **Inter** para toda la interfaz: texto, controles, tablas y cifras (con números tabulares
  donde se comparan en columna). Es la sustituta que usa el propio manual.
- **GeosansLight** solo para títulos de 20 px o más, cuando TIMU entregue el archivo y la
  licencia web. Tiene un único peso y trazo fino, así que no se usa en texto corrido, tablas
  ni botones de la plataforma, aunque el manual lo permita en piezas impresas.
- La escala de la Parte I (en puntos) es para piezas impresas y PDF. La escala de la interfaz,
  en píxeles, la define `DESIGN.md`.

## 13. Logo en la plataforma

- Mientras no llegue el logo en vector, se muestra el nombre **TIMU** en texto, en marino sobre
  claro y en blanco sobre la superficie de marca. Ese marcador no imita el logo: nada de letras
  pintadas con los colores de la T, la M y la U.
- El lema es **«Medicina veterinaria prepagada»**.
- Cuando llegue el SVG, se usa tal cual. Sobre fondo oscuro solo se usa la versión para fondo
  oscuro que entregue TIMU.

## 14. Voz en la plataforma

- **Portal, registro, encuestas y mensajes a familias:** se tutea y se aplican los dos
  registros. Cercano en bienvenidas y recordatorios; experto y preciso en salud, urgencias,
  pagos y condiciones del plan.
- **Panel del equipo:** lenguaje de trabajo, claro y sin jerga técnica (documento de
  requerimientos, sección 13). El registro juguetón no aplica.
- La lista «No decimos» rige en todo lo que ve la familia. Cuando un beneficio no tiene tope,
  se dice lo que sí tiene («sin tope de usos al mes»), no «ilimitado».

## 15. Tokens en el código

`frontend/src/styles/tokens.css` implementa este manual en tres capas:

1. **Paleta.** Los pasos de la sección 9 (`--verde-500`, `--marino-600`…). Solo se nombran
   dentro de `tokens.css`.
2. **Roles.** Los de la sección 10. Son lo único que usan los componentes, las vistas y los
   `style={{}}`.
3. **Pares permitidos.** Cada combinación de texto y fondo, o de control y fondo, con su mínimo.
   La prueba de la suite del panel los recalcula.

**Ampliar la paleta o los roles** se hace en este orden: añadir el paso a la paleta (si falta)
con su origen y su función en la sección 9, añadir el rol en la sección 10, y declarar sus pares
con su mínimo. Si un par no llega, la prueba falla antes del commit. Un cambio de color que no
pasa por aquí no se acepta.

La guarda automática hará fallar la suite si:

- aparece un color escrito a mano (`#hex`, `rgb()`, `hsl()`, `oklch()` o un nombre de color)
  en `src/` fuera de `tokens.css`;
- un componente usa un paso de la paleta en lugar de un rol;
- se usa un `var(--…)` que no está definido;
- un par declarado queda por debajo de su mínimo, o un rol de texto o de borde no tiene ningún
  par declarado.

Además, Playwright recorre todas las rutas a 375, 768 y 1280 px. Falla si algo desborda la
pantalla en horizontal o si `axe-core` encuentra un contraste insuficiente en la página ya
dibujada.

> Estado a 2026-11-10: las tres capas están en `tokens.css` (`R1-TOK-01`) y la guarda las
> vigila. Con la paleta de la marca, el recorrido de Playwright ya no encuentra ningún fallo de
> contraste; quedan nueve desbordes del responsive anterior, que resuelve el rediseño de cada
> pantalla.
