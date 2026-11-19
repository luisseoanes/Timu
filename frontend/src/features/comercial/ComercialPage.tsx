import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Pestanas } from '@/components/Pestanas'

import { Conversaciones } from './Conversaciones'
import { FichaInteresado } from './FichaInteresado'
import { InteresadosLista } from './InteresadosLista'

/** Comercial (R2-PAN-09): los interesados en listado con ficha, como Familias, y las conversaciones
 * que esperan a un asesor. El guion del asistente lo edita Administración. */
export function ComercialPage() {
  const [params] = useSearchParams()
  const abierto = params.get('interesado')
  // El Inicio de Comercial lleva a las conversaciones que esperan a un asesor (`?pestana=`).
  const [pestana, setPestana] = useState(params.get('pestana') === 'conversaciones' ? 'conversaciones' : 'interesados')
  // La ficha vive en Interesados: abrir uno desde otra pestaña («Abrir conversación») la trae.
  const [visto, setVisto] = useState(abierto)
  if (abierto !== visto) {
    setVisto(abierto)
    if (abierto) setPestana('interesados')
  }
  const pestanas = [
    { valor: 'interesados', titulo: 'Interesados', contenido: <Interesados /> },
    { valor: 'conversaciones', titulo: 'Conversaciones', contenido: <Conversaciones /> },
  ]
  return <Pestanas etiqueta="Secciones comerciales" pestanas={pestanas} valor={pestana} onCambio={setPestana} />
}

/** El interesado abierto vive en la URL (`?interesado=`), como la familia o la ruta abierta. */
function Interesados() {
  const [params] = useSearchParams()
  const abierto = params.get('interesado')
  return (
    <div className="con-ficha" data-abierta={abierto ? 'true' : undefined}>
      <InteresadosLista seleccionado={abierto} />
      {abierto ? (
        // La clave reinicia la ficha al cambiar de interesado: el texto a medio escribir no pasa a otro.
        <FichaInteresado key={abierto} id={abierto} />
      ) : (
        <section className="ficha-abierta ficha-vacia" aria-label="Interesado abierto">
          <p>Abre un interesado para ver dónde va en el embudo, qué toca y su conversación de WhatsApp.</p>
        </section>
      )}
    </div>
  )
}
