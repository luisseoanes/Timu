import { Consulta } from '@/components/Consulta'
import { fecha } from '@/lib/formato'
import type { DocumentoRead } from '@/types'

import { useMiFamilia, useMisDocumentos } from './api'

const TIPOS: Record<DocumentoRead['origen'], string> = {
  subido: 'Documento',
  contrato: 'Contrato',
  carnet: 'Carnet',
  adjunto_clinico: 'Adjunto clínico',
  formula: 'Fórmula médica',
}

/** 6.1 Los documentos de la familia en su portal: contratos, carnets y lo que el equipo comparte. */
export function DocumentosPortal() {
  const documentos = useMisDocumentos()
  const familia = useMiFamilia()
  const mascota = (id: string | null | undefined) =>
    id ? (familia.data?.mascotas?.find((m) => m.id === id)?.nombre ?? '') : ''

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Mis documentos</h3>
      </div>
      <Consulta
        consulta={documentos}
        cargando="Cargando tus documentos…"
        error="No fue posible cargar tus documentos."
        vacio="Todavía no tienes documentos."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ul className="pila" aria-label="Mis documentos">
            {d.map((doc) => (
              <li key={doc.archivo_id}>
                {doc.url ? (
                  <a href={doc.url} target="_blank" rel="noreferrer">
                    {doc.descripcion ?? doc.nombre}
                  </a>
                ) : (
                  <span>{doc.descripcion ?? doc.nombre}</span>
                )}
                <span className="apagado">
                  {' · '}
                  {[TIPOS[doc.origen], mascota(doc.mascota_id), fecha(doc.creado_en.slice(0, 10))].filter(Boolean).join(' · ')}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Consulta>
    </section>
  )
}
