# Estimación de costos de infraestructura e integraciones

Foto del **10 de noviembre de 2026**: la estimación que se entregó en PDF a la product owner
de TIMU, con sus supuestos y fuentes, para poder revisarla o rehacerla con otros números. Los
precios se consultaron ese día en las páginas oficiales de cada proveedor. Antes de contratar
hay que confirmarlos en la calculadora de cada nube.

## Base de cálculo

Movimiento reportado por TIMU para el último mes, y el volumen a 12 meses de la prueba de
carga (5.000 familias, ver [prueba de carga](prueba-de-carga.md)):

| Concepto | Hoy | A 12 meses |
| --- | ---: | ---: |
| Clientes activos (cuotas al mes) | 560 | 5.000 |
| Servicios al mes (14 asesorías virtuales, 135 desparasitaciones, 25 vacunaciones, 42 consultas, 24 imagenología) | 240 | 2.143 |
| Visitas domiciliarias (rutas) | 226 | 2.018 |
| Mensajes de WhatsApp de utilidad y autenticación | 1.230 | 10.982 |
| Mensajes de WhatsApp de marketing (1 campaña al mes) | 560 | 5.000 |
| Tokens de IA al mes (entrada / salida) | 492.000 / 141.000 | 4.392.857 / 1.258.929 |

Los mensajes de WhatsApp salen de las plantillas que envía el sistema ([integraciones](integraciones.md)):
- dos avisos por visita, de llegada y de técnico en camino;
- una encuesta por servicio;
- un recordatorio por evento preventivo;
- avisos de cobro, suponiendo 15 % de clientes en mora;
- bienvenida y enlace de afiliación, suponiendo 30 altas al mes;
- códigos de ingreso al portal.

La IA supone unas 300 consultas al bot comercial y 14 borradores al mes.

## Resultado

Costo mensual de nube más integraciones. No incluye la comisión de pagos (aparte) ni el IVA.

| Alternativa | Hoy | Hoy (COP) | A 12 meses | Por cliente hoy (COP) |
| --- | ---: | ---: | ---: | ---: |
| AWS | US$ 128,31 | $ 414.433 | US$ 454,52 | $ 740 |
| **Google Cloud (recomendada)** | **US$ 85,59** | **$ 276.451** | **US$ 428,19** | **$ 494** |
| Railway | US$ 41,77 | $ 134.912 | US$ 276,13 | $ 241 |

**Recomendación: Google Cloud.** Tiene base de datos administrada con respaldos automáticos
y un camino directo a alta disponibilidad, y comparte factura con Gemini. Railway es lo más
barato y ya aloja el entorno de pruebas, pero da menos garantías para datos personales y
clínicos en producción. AWS es lo más completo y lo más caro a este tamaño, por costos fijos
que no dependen del uso: el balanceador y las IPs públicas suman unos US$ 40 al mes.

## Infraestructura por alternativa

Las tres despliegan el mismo stack del entorno de desarrollo: API, worker, programador,
panel estático, PostgreSQL 18 con PgBouncer, Redis y almacenamiento S3.

### AWS (US East, Virginia del Norte)

| Componente | Servicio | Hoy | | A 12 meses | |
| --- | --- | --- | ---: | --- | ---: |
| API | ECS Fargate (ARM) | 0,5 vCPU · 1 GB | US$ 14,45 | 2 × 1 vCPU · 2 GB | US$ 57,82 |
| Worker (tareas, rutas) | ECS Fargate (ARM) | 0,5 vCPU · 1 GB | US$ 14,45 | 1 vCPU · 2 GB | US$ 28,91 |
| Programador (beat) | ECS Fargate (ARM) | 0,25 vCPU · 0,5 GB | US$ 7,23 | 0,25 vCPU · 0,5 GB | US$ 7,23 |
| PostgreSQL 18 | RDS db.t4g.small / medium | 1 zona · 20 GB | US$ 25,66 | t4g.medium Multi-AZ · 50 GB | US$ 106,40 |
| Redis (colas) | ElastiCache Valkey | t4g.micro | US$ 9,34 | t4g.small | US$ 18,69 |
| Balanceador HTTPS | Application Load Balancer | 1 LCU | US$ 22,27 | 2 LCU | US$ 28,11 |
| IPs públicas | IPv4 pública | 5 direcciones | US$ 18,25 | 6 direcciones | US$ 21,90 |
| Archivos y respaldos | S3 Standard + Standard-IA | 20 GB + 30 GB | US$ 1,33 | 150 GB + 100 GB | US$ 6,20 |
| Panel web | S3 + CloudFront | capa gratuita | US$ 0,00 | capa gratuita | US$ 0,00 |
| Registros | CloudWatch Logs | 5 GB | US$ 2,80 | 20 GB | US$ 11,20 |
| Secretos | Secrets Manager | 8 secretos | US$ 3,20 | 8 secretos | US$ 3,20 |
| Tráfico de salida | Data transfer out | < 100 GB (gratis) | US$ 0,00 | 200 GB | US$ 9,00 |
| **Total** | | | **US$ 118,99** | | **US$ 298,64** |

### Google Cloud (us-central1 o us-east1)

La API corre en Cloud Run con una instancia mínima. El worker, el programador, Redis y
PgBouncer comparten una máquina virtual con Docker, mucho más barata a este tamaño que
servicios administrados separados (Memorystore costaría unos US$ 36 más al mes).

| Componente | Servicio | Hoy | | A 12 meses | |
| --- | --- | --- | ---: | --- | ---: |
| API | Cloud Run | 1 vCPU · 1 GiB, mín. 1 | US$ 12,96 | 1 vCPU · 2 GiB, mín. 2 | US$ 65,38 |
| Worker + beat + Redis + PgBouncer | Compute Engine (Docker) | e2-medium · 30 GB | US$ 27,46 | e2-standard-2 · 50 GB | US$ 53,91 |
| PostgreSQL 18 | Cloud SQL Enterprise | db-g1-small · 20 GB | US$ 31,00 | 1 vCPU · 3,75 GB, alta disp. · 50 GB | US$ 119,62 |
| Balanceador HTTPS | Cloud Load Balancing | URL de Cloud Run (gratis) | US$ 0,00 | 1 regla | US$ 18,25 |
| Archivos y respaldos | Cloud Storage Standard + Nearline | 20 GB + 30 GB | US$ 0,70 | 150 GB + 100 GB | US$ 4,00 |
| Panel web | Firebase Hosting | capa gratuita | US$ 0,00 | capa gratuita | US$ 0,00 |
| IP de la máquina virtual | IPv4 externa | 1 dirección | US$ 3,65 | 1 dirección | US$ 3,65 |
| Registros | Cloud Logging | < 50 GiB (gratis) | US$ 0,00 | ~60 GiB | US$ 2,00 |
| Secretos | Secret Manager | 8 secretos | US$ 0,50 | 8 secretos | US$ 0,50 |
| Tráfico de salida | Standard Tier | < 200 GB (gratis) | US$ 0,00 | 200 GB | US$ 5,00 |
| **Total** | | | **US$ 76,27** | | **US$ 272,31** |

La base `db-g1-small` es de núcleo compartido y no tiene acuerdo de nivel de servicio; la
columna de 12 meses ya pasa a 1 vCPU dedicada con alta disponibilidad.

### Railway

Cobra por el consumo real de CPU y memoria por minuto (US$ 20 por vCPU y US$ 10 por GB al
mes). El plan Pro cuesta US$ 20 e incluye US$ 20 de consumo.

| Componente | Servicio | Hoy | | A 12 meses | |
| --- | --- | --- | ---: | --- | ---: |
| Plan | Railway Pro | 1 puesto | US$ 20,00 | 1 puesto | US$ 20,00 |
| API | Servicio | 0,15 vCPU · 0,5 GB prom. | US$ 8,00 | 2 réplicas · 0,8 vCPU · 2 GB | US$ 36,00 |
| Worker (tareas, rutas) | Servicio | 0,10 vCPU · 0,6 GB | US$ 8,00 | 0,4 vCPU · 1,5 GB | US$ 23,00 |
| Programador (beat) | Servicio | 0,02 vCPU · 0,15 GB | US$ 1,90 | 0,02 vCPU · 0,15 GB | US$ 1,90 |
| Panel web + PgBouncer | Servicios | 0,02 vCPU · 0,1 GB | US$ 1,40 | 0,04 vCPU · 0,12 GB | US$ 2,60 |
| PostgreSQL 18 | Servicio + volumen | 0,1 vCPU · 0,5 GB · 20 GB | US$ 10,00 | 0,5 vCPU · 2 GB · 60 GB | US$ 39,00 |
| Redis (colas) | Servicio | 0,02 vCPU · 0,1 GB | US$ 1,40 | 0,05 vCPU · 0,3 GB | US$ 4,00 |
| Archivos y respaldos | Railway Buckets | 20 GB + 30 GB | US$ 0,75 | 150 GB + 100 GB | US$ 3,75 |
| Tráfico de salida | Egress de servicios | 20 GB | US$ 1,00 | 200 GB | US$ 10,00 |
| **Total** (el plan se descuenta del consumo) | | | **US$ 32,45** | | **US$ 120,25** |

PostgreSQL corre como un servicio más, sin alta disponibilidad administrada ni recuperación
a un punto en el tiempo comparables a RDS o Cloud SQL. Los acuerdos de nivel de servicio solo
existen en los planes empresariales.

## Integraciones

| Integración | Base del cálculo | Hoy | A 12 meses |
| --- | --- | ---: | ---: |
| WhatsApp Business (Meta) | US$ 0,0008 por mensaje de utilidad o autenticación, US$ 0,0125 por marketing | US$ 7,98 | US$ 73,34 |
| Google Maps | Dentro de los 10.000 elementos gratis al mes; a 12 meses con rutas por zonas y caché | US$ 0,00 | US$ 52,55 |
| IA: Gemini 3.1 Flash-Lite (capa paga) | Bot comercial y borradores de orientación virtual | US$ 0,33 | US$ 2,99 |
| Correo transaccional (Amazon SES o similar) | Reserva para enlaces y avisos | US$ 1,00 | US$ 1,00 |
| Sentry | Plan Developer gratuito hoy; plan Team al crecer | US$ 0,00 | US$ 26,00 |
| GitHub Actions | Dentro de los minutos del plan actual | US$ 0,00 | US$ 0,00 |
| **Subtotal** | | **US$ 9,32** | **US$ 155,88** |

**Wompi (variable, aparte).** 2,65 % + $700 + IVA por pago aprobado (plan general publicado).
Con una cuota promedio supuesta de $ 60.000, cada pago cuesta unos $ 2.725, el 4,5 % del
recaudo:

| | Hoy (560 pagos) | A 12 meses (5.000 pagos) |
| --- | ---: | ---: |
| Comisión de Wompi | $ 1.526.056 (US$ 472) | $ 13.625.500 (US$ 4.218) |

Es el costo más grande, entre 3 y 10 veces el de la nube con sus integraciones. Wompi tiene
tarifas menores para otros medios (QR al 1 % desde septiembre de 2026), y conviene negociar
según el volumen.

**Google Maps.** La matriz de distancias crece con el cuadrado de las visitas que se
planifican juntas: sin planificar por zonas pediría unos 145.000 elementos al mes a 12 meses.
El código la acota con `MAPS_TOPE_DIARIO` (2.000 elementos al día, unos 60.000 al mes), así
que el gasto no pasa de unos **US$ 250 al mes**. Pasado el tope, el sistema estima las
distancias y las rutas salen peores ([integraciones](integraciones.md)).

## IA: comparativa

Precios por millón de tokens en la capa paga, y costo mensual con el volumen de arriba. La
decisión de usar Gemini y lo que falta para hacerlo están en
[pendientes externos](pendientes-externos.md).

| Modelo | Proveedor | Entrada | Salida | Mes hoy | Mes a 12 m | Uso sugerido |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Gemini 3.1 Flash-Lite | Google | US$ 0,25 | US$ 1,50 | US$ 0,33 | US$ 2,99 | Recomendado |
| Gemini 2.5 Flash-Lite | Google | US$ 0,10 | US$ 0,40 | US$ 0,11 | US$ 0,94 | Generación anterior, riesgo de retiro |
| Gemini 3.8 Flash | Google | US$ 0,75 | US$ 3,75 | US$ 0,90 | US$ 8,02 | Más calidad; precio se duplica el 1-ene-2027 |
| Claude Haiku 5.5 | Anthropic | US$ 0,10 | US$ 0,50 | US$ 0,12 | US$ 1,07 | Ya integrado: solo cambiar `IA_MODELO` |
| Claude Sonnet 5.5 | Anthropic | US$ 2,00 | US$ 10,00 | US$ 2,39 | US$ 21,38 | Calidad alta |
| Claude Opus 5.5 | Anthropic | US$ 4,00 | US$ 20,00 | US$ 4,79 | US$ 42,75 | Configurado hoy por defecto: sobredimensionado |
| GPT-6 Luna | OpenAI | US$ 0,10 | US$ 0,50 | US$ 0,12 | US$ 1,07 | Otro conector por desarrollar |
| GPT-5 nano | OpenAI | US$ 0,05 | US$ 0,40 | US$ 0,08 | US$ 0,72 | Generación anterior con retiro anunciado |

A este volumen la diferencia entre los modelos económicos es de centavos al mes. Pesan más
la calidad de los borradores clínicos, el tratamiento de los datos (solo capa paga: la
gratuita de Gemini usa los datos para mejorar productos de Google) y el trabajo de
integración.

## Supuestos y exclusiones

- **Tasa de cambio:** TRM de referencia $ 3.230 por dólar (5 a 7 de noviembre de 2026).
- **Impuestos:** sin IVA. Los servicios digitales prestados desde el exterior pagan 19 % de
  IVA cuando se facturan a una empresa colombiana.
- **Precios de lista a demanda,** sin compromisos ni créditos. Con compromisos de 1 año, AWS
  y Google Cloud bajan entre 25 % y 40 % en cómputo y base de datos.
- **Dimensionamiento:** «hoy» atiende el movimiento reportado con holgura; «a 12 meses» supone
  5.000 familias y 20 usuarios simultáneos, el escenario de la prueba de carga.
- **Región:** ningún proveedor tiene región en Colombia. São Paulo, la más cercana de AWS,
  cuesta entre 30 % y 50 % más que Virginia.
- **No incluye:** desarrollo, soporte y mantenimiento; la adaptación del conector de IA a
  Gemini; licencias de herramientas del equipo; el dominio, que TIMU ya tiene comprado
  (`.com.co`); ni el trámite de verificación de WhatsApp Business.
- **Riesgos de precio:** Meta revisa las tarifas de WhatsApp cada trimestre; Google duplica el
  1 de enero de 2027 los precios introductorios de Gemini 3.8 Flash; el costo de Google Maps
  crece con el cuadrado de las visitas que se planifican juntas, hasta el tope diario.

## Fuentes

Consultadas el 10 de noviembre de 2026:

- AWS: [Fargate](https://aws.amazon.com/fargate/pricing/), [RDS PostgreSQL](https://aws.amazon.com/rds/postgresql/pricing/),
  [ElastiCache](https://aws.amazon.com/elasticache/pricing/), [balanceadores](https://aws.amazon.com/elasticloadbalancing/pricing/).
- Google Cloud: [Cloud Run](https://cloud.google.com/run/pricing), [Cloud SQL](https://cloud.google.com/sql/pricing),
  [Compute Engine](https://cloud.google.com/compute/vm-instance-pricing).
- Railway: [precios](https://docs.railway.com/pricing), [Buckets](https://docs.railway.com/storage-buckets/billing).
- IA: [Gemini API](https://aistudio.google.com/docs/pricing), [OpenAI](https://developers.openai.com/api/docs/pricing),
  [Claude](https://platform.claude.com/docs/en/about-claude/pricing).
- [WhatsApp Business Platform](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing)
  y la [tarjeta de tarifas por país de noviembre de 2026](https://www.salesforce.com/en-us/wp-content/uploads/sites/4/Salesforce-Message-Credits-WhatsApp-Rate-Card-per-message-Nov-2026.pdf).
- [Google Maps Platform](https://developers.google.com/maps/billing-and-pricing/pricing).
- Wompi: plan general publicado por Wompi y Bancolombia; tarifa QR en
  [Enter.co](https://www.enter.co/?p=587327).
- TRM: [dolar-colombia.com](https://www.dolar-colombia.com/2026-11-06) y Banco de la República.

Las tarifas de RDS, ElastiCache, balanceadores, Cloud Run y Cloud SQL son precios de lista
publicados; las de WhatsApp para Colombia son de referencia, porque Meta las actualiza cada
trimestre.
