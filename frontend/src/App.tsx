import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider } from '@/features/auth/AuthContext'
import { LoginPage } from '@/features/auth/LoginPage'
import { RecuperarPage, RestablecerPage } from '@/features/auth/RecuperarPage'
import { AfiliacionPage, AfiliacionResultadoPage } from '@/features/publico/AfiliacionPage'
import { EncuestaPage } from '@/features/publico/EncuestaPage'
import { VerificarCarnetPage } from '@/features/publico/VerificarCarnetPage'
import type { Rol } from '@/types'
import { CarteraPage } from '@/features/cartera/CarteraPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { FamiliaDetallePage } from '@/features/familias/FamiliaDetallePage'
import { FamiliasPage } from '@/features/familias/FamiliasPage'
import { ClinicaPage } from '@/features/clinica/ClinicaPage'
import { EntradaPage } from '@/features/clinica/EntradaPage'
import { HistoriaMascotaPage } from '@/features/clinica/HistoriaMascotaPage'
import { Placeholder } from '@/features/Placeholder'
import { PreventivosPage } from '@/features/preventivos/PreventivosPage'
import { RutasPage } from '@/features/rutas/RutasPage'
import { ServicioDetallePage } from '@/features/servicios/ServicioDetallePage'
import { ServiciosPage } from '@/features/servicios/ServiciosPage'
import { TareasPage } from '@/features/tareas/TareasPage'
import { AppLayout } from '@/layouts/AppLayout'
import { ProtectedRoute } from '@/routes/ProtectedRoute'

// El panel es del equipo interno; las familias y las aliadas tienen su propio espacio.
const EQUIPO: Rol[] = ['admin', 'comercial', 'operaciones', 'medico']

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/recuperar" element={<RecuperarPage />} />
            <Route path="/restablecer" element={<RestablecerPage modo="restablecer" />} />
            <Route path="/activar" element={<RestablecerPage modo="activar" />} />
            <Route path="/encuesta/:token" element={<EncuestaPage />} />
            <Route path="/verificar/:codigo" element={<VerificarCarnetPage />} />
            <Route path="/afiliacion" element={<AfiliacionPage />} />
            <Route path="/afiliacion/resultado" element={<AfiliacionResultadoPage />} />
            <Route element={<ProtectedRoute roles={EQUIPO} />}>
              <Route element={<AppLayout />}>
                <Route index element={<DashboardPage />} />
                <Route path="familias" element={<FamiliasPage />} />
                <Route path="familias/:id" element={<FamiliaDetallePage />} />
                <Route path="cartera" element={<CarteraPage />} />
                <Route path="servicios" element={<ServiciosPage />} />
                <Route path="servicios/:id" element={<ServicioDetallePage />} />
                <Route path="tareas" element={<TareasPage />} />
                <Route path="preventivos" element={<PreventivosPage />} />
                <Route path="clinica" element={<ClinicaPage />} />
                <Route path="clinica/mascotas/:mascotaId" element={<HistoriaMascotaPage />} />
                <Route path="clinica/historias/:id" element={<EntradaPage />} />
                <Route path="rutas" element={<RutasPage />} />
                <Route
                  path="campanas"
                  element={
                    <Placeholder
                      titulo="Campañas"
                      ticket="F3-CAM"
                      detalle="Segmentación, envío masivo y trazabilidad (6.16, 6.18 y 6.19)."
                    />
                  }
                />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
