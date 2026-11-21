import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { type ComponentType, lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider, LoginPage, RecuperarPage, RestablecerPage } from '@/features/auth'
import {
  CompletarRegistroPage,
  EncuestaPage,
  PlanPage,
  PortadaPage,
  RegistroPage,
  RegistroResultadoPage,
  VerificarCarnetPage,
} from '@/features/publico'
import { CargandoPantalla } from '@/components/CargandoPantalla'
import { AppLayout } from '@/layouts/AppLayout'
import { PERFILES_EQUIPO, PERMISOS } from '@/lib/permisos'
import { AlPanel } from '@/routes/AlPanel'
import { DIRECCIONES_VIEJAS, MODULOS_DEL_PANEL } from '@/routes/modulos'
import { ProtectedRoute } from '@/routes/ProtectedRoute'
import { DeLaWebVieja } from '@/routes/WebVieja'


// El paquete va partido (auditoría de R4-CIE-02: uno solo de 998 kB, y la portada descargaba el
// panel entero): las páginas públicas y el ingreso cargan con la app; cada módulo del panel, el
// portal y la clínica aliada, al abrirse. La pantalla carga dentro de su layout (CargandoPantalla).

// Un cargador por módulo (cada uno es un trozo del paquete) y sus páginas, al abrirse.
const admin = () => import('@/features/admin')
const aliadas = () => import('@/features/aliadas')
const campanas = () => import('@/features/campanas')
const cartera = () => import('@/features/cartera')
const clinica = () => import('@/features/clinica')
const comercial = () => import('@/features/comercial')
const dashboard = () => import('@/features/dashboard')
const familias = () => import('@/features/familias')
const portal = () => import('@/features/portal')
const preventivos = () => import('@/features/preventivos')
const rutas = () => import('@/features/rutas')
const servicios = () => import('@/features/servicios')
const tareas = () => import('@/features/tareas')

/**
 * La página `nombre` del módulo que carga `cargar`, cuando se abre por primera vez. Devuelve el tipo de
 * la página, para que sus props se sigan comprobando; `lazy` solo pide que sea un componente.
 */
function perezosa<M, K extends keyof M>(cargar: () => Promise<M>, nombre: K): M[K] {
  return lazy(async () => ({ default: (await cargar())[nombre] as unknown as ComponentType })) as unknown as M[K]
}

const AdminPage = perezosa(admin, 'AdminPage')
const AliadasPage = perezosa(aliadas, 'AliadasPage')
const MiClinicaPage = perezosa(aliadas, 'MiClinicaPage')
const CampanasPage = perezosa(campanas, 'CampanasPage')
const EncuestasPage = perezosa(campanas, 'EncuestasPage')
const MensajesPage = perezosa(campanas, 'MensajesPage')
const CarteraPage = perezosa(cartera, 'CarteraPage')
const ClinicaPage = perezosa(clinica, 'ClinicaPage')
const EntradaPage = perezosa(clinica, 'EntradaPage')
const HistoriaMascotaPage = perezosa(clinica, 'HistoriaMascotaPage')
const ComercialPage = perezosa(comercial, 'ComercialPage')
const DashboardPage = perezosa(dashboard, 'DashboardPage')
const FamiliaDetallePage = perezosa(familias, 'FamiliaDetallePage')
const FamiliasPage = perezosa(familias, 'FamiliasPage')
const PortalAgregarPeludo = perezosa(portal, 'PortalAgregarPeludo')
const PortalCitas = perezosa(portal, 'PortalCitas')
const PortalDatos = perezosa(portal, 'PortalDatos')
const PortalInicio = perezosa(portal, 'PortalInicio')
const PortalLayout = perezosa(portal, 'PortalLayout')
const PortalMascota = perezosa(portal, 'PortalMascota')
const PortalMascotas = perezosa(portal, 'PortalMascotas')
const PortalPagos = perezosa(portal, 'PortalPagos')
const GestionarPreventivo = perezosa(preventivos, 'GestionarPreventivo')
const PreventivosPage = perezosa(preventivos, 'PreventivosPage')
const RutasPage = perezosa(rutas, 'RutasPage')
const ServicioDetallePage = perezosa(servicios, 'ServicioDetallePage')
const ServiciosPage = perezosa(servicios, 'ServiciosPage')
const TareasPage = perezosa(tareas, 'TareasPage')

// El panel es del equipo interno; las familias y las aliadas tienen su propio espacio.

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          {/* El portal y la clínica aliada cargan con su layout: hasta tenerlo, el esqueleto. */}
          <Suspense fallback={<CargandoPantalla />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/recuperar" element={<RecuperarPage />} />
            <Route path="/restablecer" element={<RestablecerPage modo="restablecer" />} />
            <Route path="/activar" element={<RestablecerPage modo="activar" />} />
            <Route path="/encuesta/:token" element={<EncuestaPage />} />
            <Route path="/verificar/:codigo" element={<VerificarCarnetPage />} />
            <Route path="/afiliacion" element={<RegistroPage />} />
            <Route path="/afiliacion/resultado" element={<RegistroResultadoPage />} />
            <Route path="/afiliacion/completar" element={<CompletarRegistroPage />} />
            {/* La portada pública (R3-PUB-04): el punto de acceso a todo. El panel vive en /panel. */}
            <Route index element={<PortadaPage />} />
            <Route path="/planes/:plan" element={<PlanPage />} />

            <Route path="panel" element={<ProtectedRoute roles={PERFILES_EQUIPO} />}>
              <Route element={<AppLayout />}>
                <Route index element={<DashboardPage />} />
                {/* Cada módulo, solo para los perfiles que lo tienen (Sección 12): el mismo permiso
                    que su entrada del menú y que la API. */}
                <Route element={<ProtectedRoute roles={[...PERMISOS.verFamilias]} />}>
                  <Route path="familias" element={<FamiliasPage />} />
                  <Route path="familias/:id" element={<FamiliaDetallePage GestionarPreventivo={GestionarPreventivo} />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.verCartera]} />}>
                  <Route path="cartera" element={<CarteraPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.servicios]} />}>
                  <Route path="servicios" element={<ServiciosPage />} />
                  <Route path="servicios/:id" element={<ServicioDetallePage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.tareas]} />}>
                  <Route path="tareas" element={<TareasPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.preventivos]} />}>
                  <Route path="preventivos" element={<PreventivosPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.clinico]} />}>
                  <Route path="clinica" element={<ClinicaPage />} />
                  <Route path="clinica/mascotas/:mascotaId" element={<HistoriaMascotaPage />} />
                  <Route path="clinica/historias/:id" element={<EntradaPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.campo]} />}>
                  <Route path="rutas" element={<RutasPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.mercadeo]} />}>
                  <Route path="comercial" element={<ComercialPage />} />
                  <Route path="campanas" element={<CampanasPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.mensajes]} />}>
                  <Route path="mensajes" element={<MensajesPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.encuestas]} />}>
                  <Route path="encuestas" element={<EncuestasPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.aliadas]} />}>
                  <Route path="aliadas" element={<AliadasPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.administrar]} />}>
                  <Route path="admin" element={<AdminPage />} />
                </Route>
              </Route>
            </Route>

            <Route element={<ProtectedRoute roles={['familia']} />}>
              <Route path="portal" element={<PortalLayout />}>
                <Route index element={<PortalInicio />} />
                <Route path="mascotas" element={<PortalMascotas />} />
                <Route path="mascotas/nueva" element={<PortalAgregarPeludo />} />
                <Route path="mascotas/:mascotaId" element={<PortalMascota />} />
                <Route path="citas" element={<PortalCitas />} />
                <Route path="pagos" element={<PortalPagos />} />
                {/* Regreso desde la pasarela: el estado real llega por webhook. */}
                <Route path="pagos/:pagoId" element={<PortalPagos />} />
                <Route path="datos" element={<PortalDatos />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute roles={['aliada']} />}>
              <Route path="aliada" element={<MiClinicaPage />} />
            </Route>

            {/* Las direcciones del panel antes de que la portada ocupara la raíz (R3-PUB-04). */}
            {MODULOS_DEL_PANEL.map((m) => (
              <Route key={m} path={`${m}/*`} element={<AlPanel />} />
            ))}
            {DIRECCIONES_VIEJAS.map((d) => (
              <Route key={d} path={d} element={<DeLaWebVieja />} />
            ))}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </Suspense>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
