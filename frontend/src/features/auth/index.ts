// Superficie pública del dominio: lo único que otros dominios y la composición
// (App, layouts) importan de aquí. Lo demás es interno (ver docs/frontend/conventions.md).
export { AuthProvider, useAuth } from './AuthContext'
export { LoginPage } from './LoginPage'
export { RecuperarPage, RestablecerPage } from './RecuperarPage'
export { useEquipo } from './api'
