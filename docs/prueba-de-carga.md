# Prueba de carga

Mide el volumen proyectado a 12 meses (5.000 familias, un año de cartera, servicios y
mensajes) con 20 usuarios simultáneos, y falla si el p95 pasa de 500 ms en las consultas o
de 2 s en el dashboard, o si falla más del 1 % de las peticiones (F4-QAA-02). Mete datos
sintéticos en la base, así que se corre en un proyecto aparte:

```bash
docker compose stop
docker compose -p timu-carga up --build -d
docker compose -p timu-carga exec api python -m scripts.datos_demo
docker compose -p timu-carga exec api python -m scripts.datos_volumen   # ~1 min; --escala para otro tamaño
docker compose -p timu-carga --profile carga run --rm carga             # k6, 5 min; CARGA_VUS y CARGA_DURACION
docker compose -p timu-carga down -v --rmi local && docker compose up -d
```

El escenario está en `infra/carga/recorrido.js`. Cada usuario virtual ingresa con su propio
usuario (`datos_volumen` crea 25 del equipo y 25 del portal) y deja de 1 a 3 s entre
peticiones: con una sesión compartida se mediría el límite de 120 peticiones por minuto y
por usuario, no la aplicación. El CI corre una versión reducida (10 % del volumen, 4
usuarios, 1 minuto) en el job del stack.

Resultados y decisiones de la puesta a punto (umbrales, volumen, por qué un usuario por usuario virtual) en el registro de la fase 5 de [plan-persistencia.md](plan-persistencia.md).
