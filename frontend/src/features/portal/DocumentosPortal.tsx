import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { diaISO, fechaCortaConDia } from '@/lib/formato'
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
    <section className="portal-panel" aria-labelledby="documentos-titulo">
      <h2 id="documentos-titulo" className="portal-panel-titulo">
        Tus documentos
      </h2>
      <Consulta
        consulta={documentos}
        cargando="Cargando tus documentos…"
        error="No pudimos cargar tus documentos."
        vacio="Todavía no tienes documentos. Aquí aparecen los carnets en PDF y lo que el equipo comparte contigo."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ul className="portal-lista" aria-label="Tus documentos">
            {d.map((doc) => (
              <li key={doc.archivo_id}>
                <span>
                  {doc.url ? (
                    <a href={doc.url} target="_blank" rel="noreferrer">
                      <Icono nombre="descargar" size={16} /> {doc.descripcion ?? doc.nombre}
                    </a>
                  ) : (
                    <strong>{doc.descripcion ?? doc.nombre}</strong>
                  )}
                  <span className="apagado">
                    {[TIPOS[doc.origen], mascota(doc.mascota_id), fechaCortaConDia(diaISO(doc.creado_en))].filter(Boolean).join(' · ')}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </Consulta>
    </section>
  )
}
