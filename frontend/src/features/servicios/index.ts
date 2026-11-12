// Superficie pública del dominio: lo único que otros dominios y la composición
// (App, layouts) importan de aquí. Lo demás es interno (ver docs/frontend/conventions.md).
export { ServicioDetallePage } from './ServicioDetallePage'
export { ServiciosPage } from './ServiciosPage'
export { useDisponibilidad, usePasos, useServicios } from './api'
