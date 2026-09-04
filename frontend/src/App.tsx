import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider } from '@/features/auth/AuthContext'
import { LoginPage } from '@/features/auth/LoginPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { FamiliasPage } from '@/features/familias/FamiliasPage'
import { Placeholder } from '@/features/Placeholder'
import { AppLayout } from '@/layouts/AppLayout'
import { ProtectedRoute } from '@/routes/ProtectedRoute'

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
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<DashboardPage />} />
                <Route path="familias" element={<FamiliasPage />} />
                <Route
                  path="cartera"
                  element={
                    <Placeholder
                      titulo="Cartera"
                      ticket="F1-CAR"
                      detalle="Mora, congelamiento, reactivación y renovación anual (6.2 y 6.4)."
                    />
                  }
                />
                <Route
                  path="servicios"
                  element={
                    <Placeholder
                      titulo="Servicios"
                      ticket="F1-SER"
                      detalle="Programación, pendientes y máquina de estados (6.5, 6.6 y 6.10)."
                    />
                  }
                />
                <Route
                  path="preventivos"
                  element={
                    <Placeholder
                      titulo="Preventivos"
                      ticket="F2-PRE"
                      detalle="Calendario preventivo, autorizaciones y carnet digital (6.8, 6.9 y 6.15)."
                    />
                  }
                />
                <Route
                  path="clinica"
                  element={
                    <Placeholder
                      titulo="Clínica"
                      ticket="F2-CLI"
                      detalle="Historia clínica estructurada y atención virtual (6.14 y 6.17)."
                    />
                  }
                />
                <Route
                  path="rutas"
                  element={
                    <Placeholder
                      titulo="Rutas"
                      ticket="F2-RUT"
                      detalle="Planeación y optimización de rutas domiciliarias (6.7)."
                    />
                  }
                />
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
