# Recursos de marca para los PDF

Los usa `app/core/marca_pdf.py` (fuentes, paleta, logo y pie de los PDF de la plataforma).

| Fichero | Origen |
| --- | --- |
| `timu-color.svg` | Copia de `frontend/src/assets/marca/timu-color.svg` (ver su `README.md`). |
| `GeosansLight.ttf` | Tal cual, de la carpeta de marca de TIMU (`TIMU/Tipografía TIMU/`). TIMU confirmó la licencia el 2026-11-11. |
| `Inter-Regular.ttf`, `Inter-SemiBold.ttf` | Instancias estáticas (peso 400 y 600) de la Inter variable del panel. |
| `Inter-OFL.txt` | Licencia de Inter (SIL OFL 1.1), que exige acompañar la fuente. |

## Cómo se sacaron las Inter estáticas

fpdf2 necesita TTF estáticas, y el panel solo trae la variable en WOFF2
(`@fontsource-variable/inter`). Con `fontTools` (y `brotli` para leer WOFF2):

```python
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

origen = "frontend/node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2"
for peso, nombre in [(400, "Inter-Regular.ttf"), (600, "Inter-SemiBold.ttf")]:
    estatica = instancer.instantiateVariableFont(TTFont(origen), {"wght": peso})
    estatica.flavor = None
    estatica.save(f"backend/app/recursos/marca/{nombre}")
```

El subconjunto latino cubre todos los caracteres del español (tildes, ñ, ¿, ¡, ·, —).
