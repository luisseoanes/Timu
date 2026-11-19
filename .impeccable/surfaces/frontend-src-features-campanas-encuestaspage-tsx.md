---
version: 1
slug: "frontend-src-features-campanas-encuestaspage-tsx"
primary_target: "frontend/src/features/campanas/EncuestasPage.tsx"
related_targets: ["frontend/src/features/campanas/Encuestas.tsx","frontend/src/features/campanas/MensajesPage.tsx","frontend/src/features/campanas/Mensajes.tsx"]
---

# Panel del equipo · Encuestas y Mensajes (perfiles por función)

## Alcance y modo

Dos módulos que salen de Campañas el 2026-11-19 (Sección 12, `docs/perfiles-y-permisos.md`):
Encuestas (las respuestas, 6.20 y 6.21) y Mensajes (los mensajes de WhatsApp y las bajas, 6.19).
Heredan los patrones ya cerrados de Campañas (`R2-PAN-09`): tarjetas, tabla apilable, insignias.
Modo: Operate. Construcción: en código.

## Público, tarea y restricciones

- Encuestas. Atención al cliente trabaja las novedades: entra en las calificaciones de 3 o menos,
  con la familia y el servicio a un clic. Gerencia analiza: la satisfacción del mes (promedio en
  es-CO con un decimal, como el tablero, y por tipo de servicio) y todas las respuestas, sin abrir
  fichas. La configuración vive en Administración.
- Mensajes. Comercial y Atención ven lo enviado y las bajas; Comercial da de baja y solo Atención
  quita una baja, a pedido de la familia.
- Palabras del usuario: «quitar una baja de WhatsApp lo hace Atención al cliente»; «cada perfil ve lo
  suyo y ya».
- Restricciones: las del panel (una sola acción verde, tablas apilables, WCAG 2.2 AA).

## Direction contract

THESIS: Cada módulo es la bandeja de quien lo trabaja: Atención abre en lo que pide acción, Gerencia
en la cifra. Rechaza la pestaña compartida donde todos ven todo y nadie sabe por dónde empezar.

OWN-WORLD: El de `DESIGN.md`, como Campañas.

STORY: Atención abre Encuestas y ve primero quién calificó con 3 o menos y qué dijo, con la familia y
el servicio a un clic para resolverlo; quita el filtro si quiere ver todo. Gerencia abre en la
satisfacción del mes (promedio, respondidas sobre enviadas y por tipo de servicio) y debajo lee
todas las respuestas, sin fichas. En Mensajes, quien atiende ve lo enviado con su estado y, al lado,
las bajas: Comercial da de baja un número; Atención además la quita.

FIRST VIEWPORT: 1440×900. Encuestas de Atención: título «Encuestas» en GeosansLight, una tarjeta
«Respuestas» con el filtro «Sólo calificaciones de 3 o menos» marcado y la lista (puntaje o cómo
sigue, comentario, fecha, «Ver familia · Ver servicio»). Encuestas de Gerencia: encima, la tarjeta
«Satisfacción del mes» con promedio («3,8 / 5»), respondidas y el desglose por tipo; debajo,
«Respuestas» con el filtro sin marcar y sin enlaces. Mensajes (Comercial y Atención): la tabla
apilable de mensajes (mensaje con destino y plantilla, cuándo, estado) con su paginación, y a la
derecha la tarjeta «Dados de baja» con el campo del celular, «Agregar» y la lista de bajas, con
«Quitar» solo para Atención. A 390: todo en una columna; la tabla se apila y las bajas bajan
debajo de los mensajes.

FORM: seed: none (pinned). Hereda los patrones cerrados de Campañas (`R2-PAN-09`); la composición la
fijan las palabras del usuario: «cada perfil debería ver lo suyo y ya, en sincronía con los
requisitos» y «quitar una baja de WhatsApp lo hace Atención al cliente»; y, en la tabla aprobada de
`docs/perfiles-y-permisos.md`, «Encuestas: análisis (Gerencia), respuestas con novedad (Atención)».

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review and the verdict.
