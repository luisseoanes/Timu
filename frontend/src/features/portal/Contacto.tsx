import { Fragment } from 'react'

import { enlaceWhatsApp } from '@/lib/enlaces'
import { telefono } from '@/lib/formato'

import { useContactoTimu } from './api'

// R4-CIE-02: el portal decía «escríbenos por WhatsApp» en varias frases sin que ninguna fuera un
// enlace, y la urgencia mandaba a «la línea de emergencias» sin número. El número es el que guarda
// Administración → Datos de TIMU.

/** «Escríbenos por WhatsApp» como enlace a TIMU; sin número guardado, el texto solo. */
export function EnlaceWhatsApp({ texto = 'Escríbenos por WhatsApp' }: { texto?: string }) {
  const numero = useContactoTimu().data?.whatsapp
  if (!numero) return <>{texto}</>
  return (
    <a href={enlaceWhatsApp(numero)} target="_blank" rel="noreferrer">
      {texto}
    </a>
  )
}

const CONTACTO = /([Ee]scríbenos por WhatsApp)/

/** Un texto (también los del backend) con cada «escríbenos por WhatsApp» convertido en enlace. */
export function ConWhatsApp({ texto }: { texto: string }) {
  return (
    <>
      {texto.split(CONTACTO).map((parte, i) => (
        <Fragment key={i}>{CONTACTO.test(parte) ? <EnlaceWhatsApp texto={parte} /> : parte}</Fragment>
      ))}
    </>
  )
}

/** Qué hacer ante una urgencia: llamar al primer teléfono de TIMU o, sin teléfono, escribirle. El
 * número de urgencias propio lo tiene que dar TIMU (docs/pendientes-externos.md). */
export function Urgencias() {
  const datos = useContactoTimu().data
  const numero = datos?.telefonos[0]
  return (
    <p className="portal-aviso portal-urgencias">
      ¿Es una urgencia?{' '}
      {numero ? (
        <>
          Llámanos al <a href={`tel:${numero}`}>{telefono(numero)}</a>.
        </>
      ) : (
        <>
          <EnlaceWhatsApp />.
        </>
      )}
    </p>
  )
}
