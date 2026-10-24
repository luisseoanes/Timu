# Indicadores del dashboard gerencial

Definición acordada de cada indicador (F4-DAS-01). Es la misma que devuelve
`GET /api/v1/dashboard/definiciones` y la que va en la hoja *Definiciones* de los
exportables. Si una fórmula cambia, se cambia a la vez en
`backend/app/modules/dashboard/service.py` y en este documento.

Todos se calculan para un período (`desde`, `hasta`, en hora de Colombia) y,
opcionalmente, una ciudad. Los resultados se cachean cinco minutos.

| Código | Indicador | Fórmula | Unidad |
| --- | --- | --- | --- |
| `afiliaciones` | Afiliaciones | Contratos con fecha de inicio dentro del periodo. | contratos |
| `retiros` | Retiros | Contratos cancelados con fecha de fin dentro del periodo. | contratos |
| `vigentes` | Afiliados vigentes al cierre | Contratos iniciados hasta el fin del periodo y sin fecha de fin anterior a el. | contratos |
| `recaudo` | Recaudo | Suma de pagos aprobados con fecha de pago dentro del periodo (cualquier medio). | COP |
| `facturado` | Facturado | Suma del valor de las cuotas (no anuladas) que vencen dentro del periodo. | COP |
| `recaudo_del_facturado` | Recaudo sobre lo facturado | Valor pagado de las cuotas que vencen en el periodo / valor de esas cuotas. | proporcion |
| `mora` | Mora al cierre | Contratos vigentes con al menos una cuota vencida sin pagar al fin del periodo; porcentaje sobre vigentes y saldo vencido total. | contratos / COP |
| `cumplimiento_rutas` | Cumplimiento de rutas | Paradas completadas / paradas planeadas en rutas no canceladas del periodo; puntualidad: completadas con llegada hasta 30 min despues de la estimada. | proporcion |
| `servicios_por_tipo` | Servicios completados por tipo | Servicios en estado completado, agendados dentro del periodo, por tipo. | servicios |
| `satisfaccion` | Satisfaccion | Promedio de puntaje (1 a 5) de encuestas de satisfaccion respondidas que se enviaron en el periodo; tasa de respuesta = respondidas / enviadas. | puntaje |

## Exportables y reportes

- `GET /api/v1/dashboard/indicadores?formato=csv|xlsx` descarga cualquier consulta.
- Los reportes programados (`/api/v1/dashboard/reportes`) llegan por correo con el
  período anterior en Excel: diarios (el día anterior), semanales (los lunes, la
  semana anterior) o mensuales (el día 1, el mes anterior).
