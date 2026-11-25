# Bloque 2: cartera, planes y renovación

Las obligaciones de 6.2, 6.3 y 6.4 del [documento de
requerimientos](../documento-requerimientos-funcionales.md), una por fila, con el texto del
documento, en el orden en que se auditan. Método, tipos, veredictos y avance: [README](README.md).
Las rutas de la evidencia son relativas a la raíz del repositorio.

## 6.2. Gestión de cartera

**Auditado el 2026-11-25.**

Las filas 02 a 06 son los momentos de comunicación del sistema actual de TIMU («por ejemplo»): no
los exige por sí mismos, pero describen el proceso que la plataforma sustituye.

**Lo que hay:**
- Cada contrato emite sus cuotas solo, en su periodicidad: cada día a las 5:00, las que vencen en
  los 5 días siguientes (`generar_cuotas`, `backend/app/modules/cartera/service.py:160`;
  `CUOTA_EMISION_DIAS_ANTES`). Se pagan a mano desde el panel, por la pasarela (Wompi, también
  desde el portal) o con la tarjeta guardada.
- Cada día a las 6:00 (`revisar_mora`) se recalcula el estado con las reglas `cartera.estado`: en
  mora a los 5 días, congelada a los 30 y activa al ponerse al día. También se manda el aviso de
  mora más avanzado de las reglas `cartera.alerta`, a 1, 5, 15 y 25 días
  (`backend/app/modules/reglas/datos.py:24`). Todas se editan en Administración y son provisionales
  («supuestos iniciales que TIMU debe confirmar», `datos.py:1`).
- La bandeja de Cartera (`frontend/src/features/cartera/CarteraPage.tsx:24`) tiene tres vistas:
  Vencidas, Por renovar (6.4) y Todos. El Inicio de Atención y del administrador avisa de los
  contratos con cuotas vencidas.
- Lo que se le dice a la familia sale por WhatsApp con plantillas aprobadas en Meta. Las de mora
  (`cuota_vencida`, `aviso_mora` y `aviso_congelamiento`) aún no están registradas
  ([pendientes externos](../pendientes-externos.md)), así que hoy no sale ningún aviso de mora.
- **Reproducido el 2026-11-25 contra `db-test`**, con pruebas temporales que no quedaron en el
  repositorio:
  - (a) Una regla de `cartera.alerta` con «días de mora al menos −3» se guarda (201), y dos días
    antes del vencimiento no manda nada.
  - (b) Una familia sin tarjeta llega de 1 a 30 días de mora, y a congelada, sin que se cree
    ninguna tarea. Una regla de `cartera.alerta` que crea una tarea se rechaza (422).
  - (c) Una familia congelada desde julio paga lo vencido ($90.000) y vuelve a activa. Al día
    siguiente se emiten de golpe las cuotas de agosto a noviembre, ya vencidas, y la revisión la
    congela otra vez, con $180.000 vencidos y 107 días de mora.
  - (d) Un contrato semestral y uno anual emiten la cuota siguiente a los 6 y a los 12 meses, y
    ninguna en medio.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.2-01 | Identificar y hacer seguimiento a usuarios con novedades de pago | Exige | Parcial | **Identifica**: «Vencidas» lista cada contrato con cuotas vencidas, su saldo y desde cuándo, los más atrasados primero (`listar_contratos`, `backend/app/modules/cartera/service.py:641`; `test_listado_de_cartera_los_mas_atrasados_primero`, `backend/tests/test_cartera.py:555`; `test_la_bandeja_separa_la_mora_de_lo_que_esta_por_renovar`, `:596`; panel `CarteraPage.test.tsx:70`). **El seguimiento se queda en los avisos automáticos a la familia**: la mora no crea tareas (10), la gestión del equipo no se registra (20) y a los que están por pagar no se les identifica (07). |
| 6.2-02 | Momento: recordatorio previo al vencimiento | Ejemplo | Falta | No existe y no se puede configurar. La cuota se emite 5 días antes de vencer (`backend/app/modules/cartera/service.py:164`) sin avisar a nadie, y no hay plantilla declarada para un recordatorio. Las reglas `cartera.alerta` solo se evalúan con una cuota ya vencida (`avisar_mora`, `:333`). **El editor acepta una regla «antes del vencimiento» y la guarda, pero nunca se dispara** (reproducido, a). El motor rechaza al guardarla una condición sobre un dato que el evento no da (`backend/app/modules/reglas/contextos.py:6`), pero no una que no puede cumplirse nunca. Es el primer momento del proceso que TIMU tiene hoy. |
| 6.2-03 | Momento: seguimiento al vencimiento | Ejemplo | Cumple | El día siguiente al vencimiento sale el aviso «Cuota vencida» (regla `alerta_mora_1`, `backend/app/modules/reglas/datos.py:52`), que no se repite (`test_avisos_escalonados_sin_repetir`, `backend/tests/test_cartera.py:130`). Sale cuando la plantilla esté aprobada en Meta (Externo); mientras falta, se reintenta cada día (`test_sin_plantilla_el_aviso_se_reintenta`, `:143`). Con tarjeta guardada, además, se cobra al vencer (`test_cobro_recurrente_con_reintentos`, `:386`), aunque ninguna pantalla registra la tarjeta (10). |
| 6.2-04 | Momento: seguimiento a usuarios con varios días de mora | Ejemplo | Cumple | Avisos a los 5, 15 y 25 días (este último, «Aviso de congelamiento»). Si el proceso no corrió algún día, sale el más avanzado y los anteriores quedan como omitidos (misma prueba). A los 5 días el contrato pasa a «en mora» (`test_estados_por_dias_de_mora_y_reactivacion`, `:87`). Los días se editan y son provisionales. Lo que no hay es una tarea para que el equipo llame (10). |
| 6.2-05 | Momento: congelamiento del servicio según las políticas establecidas | Ejemplo | Parcial | A los 30 días se congela por una regla editable (`cartera_congelada`, `backend/app/modules/reglas/datos.py:24`): deja de emitir cuotas y avisos de mora y se le avisa a la familia (`test_congelada_no_genera_cuotas`, `:69`; la misma prueba de 04). Pero lo que se suspende está fijo en el código, lo ya agendado no se suspende (6.23-08), y el periodo congelado no tiene política: sus cuotas no se emiten, pero tampoco se perdonan (06). La política de congelamiento la tiene que decir TIMU. |
| 6.2-06 | Momento: reactivación una vez realizado el pago | Ejemplo | **Contradice** | Al pagar lo vencido, el contrato vuelve a «activa» y la familia recibe «Afiliación reactivada» (`aplicar_pago`, que llama a `reevaluar_estado`, `backend/app/modules/cartera/service.py:436`; `test_estados_por_dias_de_mora_y_reactivacion`). **Pero la reactivación dura una noche** (reproducido, c). Congelada, no se emiten cuotas (`GENERAN_CUOTAS`, `:53`), pero la emisión retoma desde la última emitida (`_emitir_pendientes`, `:180`). A la mañana siguiente salen de golpe todos los meses congelados, ya vencidos, y la familia vuelve a congelada con el doble de deuda: lo que se le pidió para reactivarse no era lo que se le iba a cobrar. Responda lo que responda TIMU sobre si esos meses se cobran, hay que cambiar cómo se emite durante el congelamiento. |
| 6.2-07 | Identificar automáticamente usuarios próximos al vencimiento | Exige | Falta | Ninguna vista, filtro ni segmento dice a quién le vence la cuota en los próximos días. La bandeja tiene Vencidas, Por renovar (la renovación del contrato, 6.4) y Todos (`CarteraPage.tsx:24`), y los segmentos de campañas filtran por días de mora y por renovación, no por el vencimiento de la cuota (`backend/app/modules/campanas/segmentos.py:36`). El dato existe (la cuota se emite 5 días antes) y se ve en cada familia, con el próximo cobro en su pestaña Cartera (`frontend/src/features/familias/CarteraFamilia.tsx:67`) y en su línea, pero hay que abrirlas una a una. |
| 6.2-08 | Identificar usuarios morosos | Exige | Cumple | La vista «Vencidas» con su recuento (01) y el estado «en mora» (6.23-02). El Inicio avisa con el más atrasado (`frontend/src/features/dashboard/DashboardPage.tsx:304`; `DashboardPage.test.tsx:220`). Además, el listado de familias se ordena por urgencia (`backend/app/modules/cartera/service.py:781`) y las campañas segmentan por días de mora (`test_filtros_combinables`, `backend/tests/test_campanas.py:57`). |
| 6.2-09 | Generar alertas | Exige | Parcial | La única alerta para el equipo es el aviso del Inicio de los contratos con cuotas vencidas (08), que se ve al entrar. Al equipo no le avisa nada de un congelamiento (solo se le escribe a la familia, `_notificar_transicion`, `backend/app/modules/cartera/service.py:301`), de una cuota por vencer (07) ni de un cobro rechazado antes de agotar los reintentos (10). Las reglas de cartera no tienen una acción de alerta al equipo: `cartera.estado` solo cambia el estado y `cartera.alerta` solo le escribe a la familia (`backend/app/modules/reglas/acciones.py:92`). Las alertas transversales, en 7 y 8. |
| 6.2-10 | Crear tareas de seguimiento | Exige | Parcial | Hay dos tareas automáticas, y las dos son del cobro con tarjeta: cuando se agotan los reintentos (`planear_cobros`, `backend/app/modules/cartera/pasarela.py:256`; `test_cobro_recurrente_agotado_crea_tarea`, `backend/tests/test_cartera.py:413`) y cuando un cobro queda sin confirmar (`:399`). **Ninguna pantalla registra una tarjeta** (`POST /cartera/medios-pago` solo lo usan las pruebas), así que en la práctica ninguna de las dos se crea. **Reproducido (b)**: una familia sin tarjeta llega a congelada sin ninguna tarea, y el motor no deja configurar una. Una tarea se puede crear a mano y atarla a la familia (`frontend/src/features/tareas/TareasPage.tsx:332`). Es justo lo que TIMU tiene hoy («una plataforma externa que genera tareas programadas según las fechas de pago»). |
| 6.2-11 | Automatizar o facilitar comunicaciones | Exige | Cumple | **Se automatizan** con reglas editables los avisos de mora (03 y 04) y los de congelamiento y reactivación (`test_estados_por_dias_de_mora_y_reactivacion`). **Se facilitan** las masivas, con campañas por días de mora o por renovación (`test_filtros_combinables`). Huecos: no hay recordatorio previo (02), y el equipo no puede escribirle a una familia desde su ficha ni desde la bandeja. `POST /comunicaciones/mensajes/plantilla` y `/texto` existen (`backend/app/modules/comunicaciones/router.py:123`), pero ninguna pantalla los usa (la fila de 6.17 y 6.19 de [lo que falta](../pendiente-en-el-codigo.md)). Nada sale sin las plantillas aprobadas en Meta. |
| 6.2-12 | Registrar pagos | Exige | Cumple | **A mano** desde la bandeja y desde la ficha, con referencia única: se aplica de la cuota más antigua a la más reciente y lo que sobra queda como saldo a favor (`registrar_pago_manual`, `backend/app/modules/cartera/service.py:440`; `test_pago_se_aplica_de_la_cuota_mas_antigua_y_sobra_saldo`, `backend/tests/test_cartera.py:162`; panel `CarteraPage.test.tsx:94` y `FamiliaDetallePage.test.tsx:196`). **Por la pasarela**, también desde el portal, con un webhook idempotente y la conciliación (`test_webhook_idempotente_y_conciliacion`, `:291`; `test_pago_en_linea_actualiza_y_da_comprobante`, `backend/tests/test_portal.py:301`). **Con la tarjeta guardada** (`:386`), que ninguna pantalla registra (10). La prueba contra el sandbox de Wompi es Externo. |
| 6.2-13 | Actualizar el estado del usuario | Exige | Cumple | `reevaluar_estado` (`backend/app/modules/cartera/service.py:258`) corre cada mañana y tras cada pago, venga de donde venga (todos pasan por `aplicar_pago`), con las reglas `cartera.estado`; la familia copia el estado de su contrato (`test_estados_por_dias_de_mora_y_reactivacion`; `test_revision_diaria`, `backend/tests/test_cartera.py:149`). Que la reactivación no dure, en 06. |
| 6.2-14 | Programar automáticamente la próxima fecha de cobro | Exige | Cumple | El día de corte es el del inicio (hasta el 28) y las cuotas se emiten sin duplicar (`generar_cuotas`, `backend/app/modules/cartera/service.py:160`; `test_contrato_con_corte_renovacion_y_primera_cuota`, `backend/tests/test_cartera.py:35`; `test_generacion_de_cuotas_es_idempotente`, `:55`). El estado de cuenta dice el próximo cobro (`test_estado_de_cuenta`, `:221`). Con la afiliación congelada no se programa nada, y según el código el «Próximo cobro» queda en una fecha ya pasada, la siguiente a la última cuota emitida (`:756`; no se reprodujo): es la causa de 06. |
| 6.2-15 | Periodicidad de pago mensual | Exige | Cumple | Es la que va por defecto (`backend/app/core/enums.py:296`), con una cuota al mes (`test_generacion_de_cuotas_es_idempotente`). Se elige al afiliar desde el panel (`FamiliaDetallePage.test.tsx:129`) y en el registro en línea (`frontend/src/features/publico/registro.test.tsx:127`). |
| 6.2-16 | Periodicidad de pago trimestral | Exige | Cumple | La cuota cubre 3 meses y la siguiente sale a los 3 meses; con un solo peludo tiene su precio propio, y con dos o más se paga el mensual por los meses (`test_trimestral_con_un_peludo_y_sin_descuento_al_sumar_otro`, `backend/tests/test_planes.py:608`; `test_un_solo_peludo_tiene_el_descuento_de_cada_periodo`, `:257`). El precio trimestral es tentativo ([pendientes externos](../pendientes-externos.md), «Precios de los planes»). |
| 6.2-17 | Periodicidad de pago semestral | Exige | Cumple | El precio se prueba en `test_un_solo_peludo_tiene_el_descuento_de_cada_periodo`, y en el panel en `FamiliaDetallePage.test.tsx:129`. La emisión cada 6 meses no tiene una prueba propia: se comprobó el 2026-11-25 contra `db-test` (d). Es el mismo código que la trimestral (`MESES_PERIODICIDAD`, `backend/app/core/enums.py:306`, y el `CHECK` `meses_periodicidad` de `cuotas`). |
| 6.2-18 | Periodicidad de pago anual | Exige | Cumple | Como 17, con su prueba de precio, en la que el anual de Colita Feliz es un precio especial que se respeta tal cual, y la emisión a los 12 meses comprobada (d). La cuota del segundo año sale aunque nadie haya renovado el contrato, y con el mismo valor (6.4). |
| 6.2-19 | Mantener historial de pagos | Exige | Cumple | Cada pago queda con su medio, referencia, estado y quién lo registró, y su aplicación a las cuotas no cambia una vez escrita (`aplicaciones_pago` en `INMUTABLES`, `backend/app/core/auditoria.py:50`). La familia ve los suyos en el portal (`test_lista_sus_pagos_y_no_paga_lo_que_no_debe`, `backend/tests/test_portal.py:472`). El panel (`CarteraFamilia.tsx:142`) tiene tres huecos. Muestra solo los 24 últimos, sin paginar (`estado_cuenta`, `backend/app/modules/cartera/service.py:719`). Ninguna prueba del panel ni del backend afirma esa lista. Y recorta el instante con `.slice(0, 10)` (`:163`), que da el día en UTC (la trampa del `CLAUDE.md` del panel): un pago hecho después de las 19:00 saldría con el día siguiente (no se comprobó). |
| 6.2-20 | Mantener historial de gestiones de cartera | Exige | Parcial | **Queda**: los mensajes enviados y recibidos, en la pestaña Comunicaciones (`test_traza_por_familia`, `backend/tests/test_comunicaciones.py:216`); los cambios de estado con su motivo, en Historial (`test_historial_de_estados`, `backend/tests/test_familias.py:186`); y cada aviso de mora con su regla, enviado u omitido (`AvisoCartera`, `backend/app/modules/cartera/models.py:197`), que ninguna pantalla muestra. **No queda la gestión del equipo**: que llamó, qué le dijo la familia, que prometió pagar el viernes. Una tarea manual atada a la familia y cerrada con su resolución es lo más parecido, pero la ficha no muestra las tareas de la familia ni la bandeja de tareas filtra por ella. Es el problema de diseño 2. |

**Lo que hay que decidir:**
- 06 y 05: qué pasa con el periodo congelado (si se cobra, si se perdona, si corre la renovación) y,
  con eso, cómo se emite durante el congelamiento. Es una pregunta para TIMU y un cambio, sea cual
  sea la respuesta.
- 02 y 07: el recordatorio previo (cuántos días antes y con qué plantilla) y la vista de los que
  están por pagar. Además, que el editor no guarde una regla que no puede dispararse nunca.
- 09 y 10: qué tareas y alertas genera la cartera para el equipo, y si una regla de cartera puede
  crearlas. Junto con eso, si el cobro con tarjeta guardada tendrá pantalla o se retira.
- 20: el registro de la gestión, junto con 6.10 y 6.8 (problema de diseño 2).

## 6.3. Cambios en planes grupales

**Auditado el 2026-11-25, con dos lecturas.**

**El documento no dice qué es un «plan grupal», y el veredicto depende de eso.** El usuario decidió
el 2026-11-25 auditarlo con las dos lecturas y pedirle a TIMU que lo aclare
([preguntas para TIMU](README.md#preguntas-para-timu)):

- **Lectura A, la del código: una familia con varios peludos.** Cada peludo tiene su plan, y todos
  pagan la tarifa de su plan para el número total de peludos, aunque estén en planes distintos. Hay
  tarifa de 1 a 4; desde 4, la de 4; como máximo, 10 (`planes.cotizar`,
  `backend/app/modules/planes/service.py:168`). El «integrante» es un peludo: retirarlo
  (`contratos.retirar_mascota`, `backend/app/modules/cartera/contratos.py:245`) pasa a los demás a
  la tarifa del nuevo número desde la siguiente cuota. Los precios por número de peludos son los de
  TIMU ([pendientes externos](../pendientes-externos.md), «Precios de los planes»).
- **Lectura B, la del texto: varias personas o familias bajo un mismo plan** (un plan de empresa,
  un grupo familiar con varios titulares). El documento llama «usuario» a la persona, nunca a la
  mascota: «identificar usuario y mascota» (6.5), «segmentar usuarios y mascotas» y «Grupo
  familiar» (6.16). No existe: un contrato es de una sola familia (`familia_vigente`,
  `backend/app/modules/cartera/models.py:58`), y los contactos adicionales no tienen plan ni acceso
  (6.1-03).

Con la lectura B todas las filas son Falta. Por eso cada fila es **Por decidir**, salvo donde las
dos lecturas dan lo mismo, y la evidencia es la de la lectura A.

**Lo que hay (lectura A):**
- El alta y la baja de un peludo con el contrato vigente las orquesta
  `backend/app/modules/afiliaciones/ciclo.py` (`dar_de_baja_mascota`, `:75`). La baja la hace el equipo desde la ficha, con un motivo; el portal
  no deja retirar un peludo.
- Cada cambio de valor queda en `cambios_plan` (`CambioPlan`, `backend/app/modules/planes/models.py:185`),
  con su tipo (`cambio_plan`, `mascota_alta` o `mascota_baja`), el valor anterior y el nuevo, la
  fecha, quién lo hizo y la regla, si la hubo. La tabla no cambia una vez escrita, salvo `aplicado`
  (`INMUTABLES`, `backend/app/core/auditoria.py:53`).
- **Reproducido el 2026-11-25 contra `db-test`**, con una prueba temporal que no quedó en el
  repositorio. En un contrato anual de dos peludos ($840.000 al año), 40 días después se retira uno
  por la API. El contrato pasa a $480.000 desde la siguiente cuota anual; la ya emitida sigue en
  $840.000, sin ajuste ni saldo a favor. Queda el registro `mascota_baja` (valores, fecha y quién,
  sin regla), y no se crea ninguna tarea ni sale ningún mensaje.

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.3-01 | Gestionar usuarios vinculados a planes grupales | Exige | Por decidir | **A: Cumple.** Se agregan y se retiran peludos, cada uno con su plan, y la composición se ve en la pestaña Cartera, con lo que paga cada uno (`frontend/src/features/familias/CarteraFamilia.tsx:78`). Pruebas: `test_con_dos_peludos_cada_uno_paga_la_tarifa_de_dos_aunque_esten_en_planes_distintos` (`backend/tests/test_planes.py:275`), `test_desde_cuatro_peludos_todos_pagan_la_tarifa_de_cuatro_y_el_maximo_es_diez` (`:298`), `test_el_cambio_de_plan_de_un_peludo_no_cambia_el_de_los_demas` (`:513`), y en el panel `FamiliaDetallePage.test.tsx:627`, `:1077` y `:1104`. **B: Falta.** |
| 6.3-02 | Al retirarse un integrante: identificar el cambio | Exige | Por decidir | **A: Cumple.** El retiro es una acción explícita del equipo, con su motivo (`POST /mascotas/{id}/baja`, `backend/app/modules/afiliaciones/router.py:245`), y queda como `mascota_baja` (reproducido, arriba). No hay otro camino: si la familia avisa por WhatsApp o en el portal, alguien del equipo tiene que hacerlo. **B: Falta.** |
| 6.3-03 | … actualizar la composición del grupo | Exige | Por decidir | **A: Cumple.** La línea del peludo queda inactiva, con su fecha de baja (`AfiliacionMascota`, `backend/app/modules/cartera/models.py:94`, con `CHECK baja_coherente`), y el contrato solo cuenta los vigentes (`contratos.lineas`, `backend/app/modules/cartera/contratos.py:38`). Prueba: `test_un_peludo_mas_baja_la_tarifa_de_todos_desde_la_siguiente_cuota` (`backend/tests/test_planes.py:555`). No se puede retirar el último peludo sin cancelar el contrato (`test_el_unico_peludo_no_se_retira_sin_cancelar_el_contrato`, `:588`). **B: Falta.** |
| 6.3-04 | … aplicar la regla correspondiente | Exige | Por decidir | **A: Parcial.** La regla de precio se aplica sola: la tarifa del nuevo número de peludos, que edita el administrador (09). **Cómo se aplica el retiro, en cambio, está fijo en el código y no consulta ninguna regla**: siempre «desde la siguiente cuota», sin devolver nada del periodo en curso (`_recalcular`, `backend/app/modules/cartera/contratos.py:159`, con `modo="proxima_cuota"`). En un contrato anual, la familia paga hasta casi un año por el peludo que ya salió (reproducido). El cambio de plan sí tiene regla (`plan.cambio`, con prorrateo o desde el periodo siguiente), y el alta desde el portal cobra el ajuste prorrateado (`backend/app/modules/afiliaciones/altas.py:96`). El alta desde el panel, según el código, no cobra nada hasta la siguiente cuota (`contratos.agregar_mascota`, `:218`): **la misma regla no se aplica igual según quién haga el cambio.** **B: Falta.** |
| 6.3-05 | … actualizar el valor a pagar | Exige | Por decidir | **A: Cumple.** El contrato y cada peludo pasan a la tarifa del nuevo número, y el valor por periodo se recalcula, también con el descuento de periodo largo cuando queda un solo peludo (`test_un_peludo_mas_baja_la_tarifa_de_todos_desde_la_siguiente_cuota`, que retira y vuelve a $35.500; `test_trimestral_con_un_peludo_y_sin_descuento_al_sumar_otro`, `backend/tests/test_planes.py:608`). Las cuotas ya emitidas no cambian (04). **B: Falta.** |
| 6.3-06 | … generar alerta o tarea | Exige | Falta | **A y B: Falta.** El retiro no crea ninguna tarea ni alerta (reproducido). Tampoco se puede configurar: no hay evento de reglas para el retiro (el de `plan.mascota` se retiró en la migración 0033, `backend/app/modules/reglas/motor.py:157`). Es el problema de diseño 4. |
| 6.3-07 | … registrar la modificación | Exige | Por decidir | **A: Parcial.** Queda registrado: el `mascota_baja` de `cambios_plan` (valores, fecha y quién, y no cambia una vez escrito), la línea inactiva del peludo con su auditoría, y su baja con el motivo (reproducido). **Pero nadie lo puede ver**: ninguna ruta lee `cambios_plan`, y el Historial de la familia solo muestra los cambios de su ficha (`familias.historial`, `backend/app/modules/familias/service.py:210`). Y ninguna prueba afirma el registro de un retiro; la que hay es la del alta (`test_un_peludo_mas_baja_la_tarifa_de_todos_desde_la_siguiente_cuota`). **B: Falta.** |
| 6.3-08 | … facilitar la comunicación al usuario | Exige | Falta | **A y B: Falta.** El retiro no le dice nada a la familia (no hay plantilla para él; reproducido), y el equipo no puede escribirle desde su ficha (6.2-11). Lo que paga desde ahora solo lo ve si entra al portal (lo de cada peludo al mes, `frontend/src/features/portal/PeludosPortal.tsx:339`). |
| 6.3-09 | Las reglas se pueden modificar después sin reconstruir la plataforma | Exige | Por decidir | **A: Parcial.** **Se cambian sin desplegar**: las tarifas por número de peludos, por periodo y por ciudad (`test_el_administrador_cambia_tarifas_y_ciudades_sin_borrar_nada`, `backend/tests/test_planes.py:341`) y la regla del cambio de plan (`test_cambio_al_proximo_ciclo_por_regla`, `:491`). **Fijo en el código**: cómo se aplica un retiro (04); el máximo de 10 peludos (`MAX_PELUDOS`, `backend/app/modules/planes/service.py:75`); y que el descuento de periodo largo no se acumule con el de cantidad (`:203`). **Fijo en la base**: los cuatro tramos (`PELUDOS_CON_DESCUENTO`, `:76`, y el `CHECK peludos_rango`, `backend/app/modules/planes/models.py:102`), así que un quinto tramo necesita una migración. La propuesta respondió «Cumple» con el motor de reglas, pero el retiro no pasa por él. **B: Falta.** |

**Lo que hay que decidir:**
- Qué es un plan grupal (pregunta para TIMU). Con la lectura B hay que construirlo entero.
- Con la lectura A: qué regla aplica al retirar un peludo (¿desde cuándo, se devuelve lo pagado del
  periodo en curso?) y que la decida una regla editable, como el cambio de plan. Y que el alta cobre
  igual desde el panel que desde el portal.
- Qué tarea, alerta o mensaje deja un retiro, y dónde se ve lo que queda en `cambios_plan`.

## 6.4. Renovación anual

| ID | Pide | Tipo | Veredicto | Evidencia y hallazgo |
| --- | --- | --- | --- | --- |
| 6.4-01 | Identificar automáticamente usuarios que cumplen un año en el plan | Exige | Sin auditar | |
| 6.4-02 | Generar alerta | Exige | Sin auditar | |
| 6.4-03 | Aplicar la regla de actualización correspondiente | Exige | Sin auditar | |
| 6.4-04 | Actualizar condiciones económicas | Exige | Sin auditar | |
| 6.4-05 | Generar tarea de comunicación | Exige | Sin auditar | |
| 6.4-06 | Registrar la renovación | Exige | Sin auditar | |
| 6.4-07 | Mantener trazabilidad | Exige | Sin auditar | |
