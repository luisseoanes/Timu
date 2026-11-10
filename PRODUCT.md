# Product

<!-- impeccable:product-schema 1 -->

> Registro de producto para la skill de diseño (`.claude/skills/impeccable`). Los títulos de
> sección siguen el formato de la skill; el contenido sigue la convención del repositorio
> (español). Lo visual vive en `DESIGN.md` y en `docs/manual-de-marca.md`, no aquí.

## Platform

web

Aplicación web responsive en todos sus espacios, sin excepción. El empaquetado como PWA
para familias es una fase posterior (propuesta, sección B).

## Users

Seis perfiles repartidos en tres espacios con acceso propio, más páginas públicas sin sesión.
Cada espacio se optimiza para su público; comparten marca y componentes, no densidad ni tono.

- **Equipo TIMU, en el panel** (`admin`, `comercial`, `operaciones`, `medico`). Es su
  herramienta de trabajo diaria: familias, cartera, servicios, tareas, preventivos, clínica,
  rutas, campañas, comercial y administración. Personal no técnico (documento de
  requerimientos, sección 13).
  - **Médicos en ruta**: usan la plataforma sobre todo desde el celular. Consultan la ruta del
    día y la historia clínica y registran la atención en casa de la familia.
  - **Administración, comercial y operaciones**: trabajo de oficina, con tablas, filtros y
    cartera.
- **Familias, en el portal** (`familia`). Personas que ven a su perro o gato como parte de la
  familia. Consultan mascotas, carnet, historia clínica, citas y pagos. Usan la plataforma sobre
  todo desde el celular, a menudo llegando desde un enlace de WhatsApp.
- **Clínica aliada** (`aliada`). Valida las remisiones de su clínica y reporta la atención.
- **Público sin sesión**: registro en línea con pago (`/afiliacion`), encuestas de
  satisfacción y verificación de carnet. Mayoritariamente desde el celular.

## Product Purpose

TIMU busca pasar de una operación repartida entre hojas de cálculo, WhatsApp, formularios y
plataformas externas a una gestión integrada y automatizada (documento de requerimientos,
secciones 1, 2 y 18). La plataforma recorre el ciclo completo:

> Captar → convertir → afiliar → gestionar → prevenir → atender → hacer seguimiento → medir → fidelizar.

Hay éxito cuando el equipo dedica menos tiempo a tareas repetitivas y a redigitar datos, la
información fluye entre procesos sin pérdida de trazabilidad, y la familia gestiona su plan,
sus pagos y sus citas sin tener que llamar.

## Positioning

TIMU es **medicina veterinaria prepagada para perros y gatos**. Facilita el acceso a la
atención veterinaria y ayuda a las familias a gestionar su costo. Combina:

- servicios propios: clínica veterinaria TIMU (Laureles, Medellín) y atención domiciliaria;
- una red de prestadores aliados en el Valle de Aburrá, algunos con atención 24 horas;
- orientación veterinaria por chat 24/7 con triage, que decide si el caso necesita consulta o
  atención presencial.

Se presenta siempre como «plan de salud prepagado» o «medicina veterinaria prepagada», nunca
como seguro (manual de marca, sección Voz).

## Operating Context

- Base de operación en Medellín y el Valle de Aburrá. La visión publicada habla de cobertura
  nacional en 2027 (meta, no situación actual).
- WhatsApp es el canal principal con las familias: orientación, recordatorios, enlaces al
  portal y a las encuestas (Meta Cloud API oficial).
- Pagos en línea y conciliación con Wompi.
- Rutas domiciliarias diarias, optimizadas con OR-Tools y Google Maps. El médico trabaja de
  pie y en casa ajena, con el celular en la mano.
- El panel se usa en oficina y en consultorio, a veces en pantallas compartidas.
- Planes vigentes: Colita Feliz, Mi Amigo Fiel y Amigos por Siempre. Sus precios, coberturas,
  topes y carencias salen del catálogo de la API; la interfaz nunca los escribe a mano.

## Capabilities and Constraints

- Alcance funcional: requisitos 6.1 a 6.23 del documento de requerimientos, más portal de
  familias, consulta de historia clínica, carnet digital, pagos en línea y autogestión de
  servicios (propuesta, sección B). El desglose ejecutable está en `docs/backlog.md`.
- Base de código existente: React 18 + TypeScript + Vite, CSS propio con tokens
  (`frontend/src/styles/tokens.css`) y primitivas de Radix para el comportamiento. Sin
  Tailwind ni librería de componentes con estilos propios.
- Terminología del dominio, siempre en español: familia, mascota (el «peludito» en la voz
  hacia las familias), afiliación, plan, cartera, mora, congelada, preventivo, carnet,
  remisión, aliada, ruta.
- Estados que la interfaz debe distinguir: afiliación (prospecto, activa, en mora, congelada,
  cancelada) y servicio (máquina de estados del requisito 6.10).
- **Por decidir (TIMU)**: logo en vector y su versión para fondo oscuro; archivo y licencia web
  de GeosansLight; términos y condiciones publicables de cada plan.

## Brand Commitments

Vinculantes por decisión del usuario:

- El manual de marca de TIMU es la base (`docs/manual-de-marca.md`, transcrito del PDF y
  ampliado con los colores auxiliares). La paleta anterior, en tonos menta, queda descartada
  por completo.
- Paleta: los cuatro colores del logo (verde `#98B833`, naranja `#D68A11`, azul `#477095`,
  marino `#111537`) con sus tintes, más los tonos auxiliares definidos en el manual del
  repositorio. Acción principal: verde con texto marino.
- Tipografía: GeosansLight solo para títulos grandes, cuando TIMU entregue el archivo y la
  licencia; Inter para todo lo demás.
- Logo: no se modifica ni se recolorea. Mientras llega en vector, se usa un marcador de texto.
- Voz con dos registros: cercano y juguetón (bienvenida, recordatorios, portal) y experto y
  preciso (salud, urgencias, condiciones del plan). Se tutea a la familia.
  - Sí: «plan de salud prepagado», «medicina veterinaria prepagada», «peludito», «peludo»,
    «la manada TIMU», descuentos con su porcentaje y su tope por episodio, exclusiones y
    carencias dichas de frente.
  - No: «seguro para mascotas», «cubrimos todo», «ilimitado», «sin costo», términos médicos
    sin explicar.

## Evidence on Hand

- Manual de marca (PDF entregado por TIMU, 8 páginas): esencia, paleta, logo, color por plan,
  tipografía, voz y tokens.
- Documento de requerimientos: `docs/documento-requerimientos-funcionales.md`.
- Web pública https://timu.com.co/ (revisada el 2026-11-10): planes con coberturas y topes,
  clínica propia, red de aliados con direcciones y horarios, canales de contacto.
- Datos de demostración sintéticos (`backend/scripts/datos_demo.py`): solo para desarrollo.

No existe y no se inventa: testimonios, cifras de familias o mascotas afiliadas, años de
trayectoria, premios o prensa. Los nombres del «equipo» que muestra la web pública
(`/nosotros/`) parecen de plantilla y no se reutilizan. El logo del PDF es una imagen de
569×308 px, sin versión vectorial.

**Contradicciones abiertas en la web pública** (las resuelve TIMU; mientras tanto manda el
manual):

- Usa «especialistas en seguros» e «ilimitado», que el manual prohíbe.
- Precios distintos entre `/planes/` y las páginas de cada plan.
- Porcentajes y frecuencias que no coinciden entre el inicio y las páginas de los planes
  (hospitalización y consultas).

## Product Principles

1. **Cada espacio sirve a su público.** El panel prioriza rapidez de lectura y pocos pasos
   para el equipo; el portal y el registro priorizan claridad y confianza para la familia; la
   clínica aliada valida y reporta sin fricción.
2. **Primero el celular donde se trabaja de pie.** Médicos en ruta, familias y páginas
   públicas se diseñan desde el móvil; el resto es plenamente responsive.
3. **Las condiciones se dicen de frente.** Porcentajes, topes, carencias y exclusiones se
   muestran completos y sin letra pequeña escondida, nunca con promesas absolutas.
4. **Nunca pedir dos veces el mismo dato.** Si la plataforma ya lo tiene, lo usa
   (requisito 6.12: formulario → pago → contrato → perfil, sin redigitación).
5. **El dato manda sobre la pantalla.** Planes, precios y coberturas salen del catálogo; la
   interfaz los presenta, no los fija.

## Accessibility & Inclusion

- WCAG 2.2 nivel AA como mínimo en todos los espacios: contraste de texto, de controles y de
  foco, operación completa con teclado y etiquetas accesibles.
- El estado nunca se comunica solo con color: lleva texto e icono.
- Lenguaje para personal no técnico y para familias sin conocimientos médicos (documento de
  requerimientos, sección 13).
- Respeto de `prefers-reduced-motion`.
