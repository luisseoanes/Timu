# Logo de TIMU

Cuatro SVG sacados del logo en vector que entregó TIMU (`Marca TIMU.ai`, primera mesa de
trabajo: el logo con el lema y las siluetas). Los pinta `MarcaTimu`
(`src/components/MarcaTimu.tsx`); el manual de marca explica cuándo va cada uno (sección 13).

| Fichero | Qué es |
| --- | --- |
| `timu-color.svg` | Completo (logotipo, lema y siluetas), a color, sobre fondo claro. |
| `timu-blanco.svg` | Completo, todo en blanco, sobre la superficie de marca. |
| `timu-compacto-color.svg` | Solo el logotipo (TIMU), a color. |
| `timu-compacto-blanco.svg` | Solo el logotipo, en blanco. |

`backend/app/recursos/marca/timu-color.svg` es una copia de `timu-color.svg` para los PDF.

## Cómo se sacaron (para regenerarlos)

El material original no vive en el repositorio: es la carpeta de marca que compartió TIMU el
2026-11-11 (ver `docs/pendientes-externos.md`). Del zip del manual se usa
`TIMU/Marca TIMU.ai`, que es un PDF por dentro.

1. `pdftocairo -svg -f 1 -l 1 "Marca TIMU.ai" color.svg` convierte la primera mesa de
   trabajo. Salen 39 trazados sin recortes: 5 letras, 28 del lema y 6 siluetas.
2. **Los colores se sustituyen por los de la paleta.** El vector está en Adobe RGB y
   `pdftocairo` lo convierte a sRGB con gestión de color, lo que da tonos más saturados de
   los que exporta la diseñadora para pantalla. Se cambia cada color convertido por el de la
   paleta (`docs/manual-de-marca.md`, sección 2):

   | Convertido por pdftocairo | Papel | En el SVG |
   | --- | --- | --- |
   | `#89B81B` | letras T, I y U | `#98B833` |
   | `#EC8200` | mitad izquierda de la M | `#D48200` |
   | `#247297` | mitad derecha de la M | `#477095` |
   | `#031135` | siluetas | `#111537` |
   | `#18264F` | lema | `#111537` |

   La versión en blanco pone `#FFFFFF` en todos los trazados.
3. **El `viewBox` se recorta** a la caja de los trazados que entran (todos para el completo,
   solo las cinco letras para el compacto), con 2 unidades de margen.
4. **Las coordenadas se redondean a enteros:** a los tamaños de pantalla una unidad es una
   fracción de píxel, y el completo baja de 70 a 52 KB.

La guarda de tokens no revisa los `.svg`: sus colores son el activo de la marca, no colores
de la interfaz.
