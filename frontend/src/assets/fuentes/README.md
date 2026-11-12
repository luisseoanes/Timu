# Fuentes servidas desde el proyecto

`geosans-light.woff2` es GeosansLight, la tipografía complementaria del manual de marca, tal
cual viene en la carpeta de marca de TIMU (`TIMU/Tipografía TIMU/GeosansLight.ttf`), pasada a
WOFF2 con `fontTools` (`TTFont(ttf).flavor = "woff2"`, más `brotli`). TIMU confirmó la licencia
el 2026-11-11. La declara el `@font-face` de `src/styles/base.css` y solo va en los títulos de
20 px o más (`--fuente-titulos`). Inter llega por `@fontsource-variable/inter`.
