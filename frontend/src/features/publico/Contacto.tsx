import { Icono } from '@/components/Icono'
import { enlaceWhatsApp } from '@/lib/enlaces'

import { useContactoRegistro } from './registro'

/** A quién escribe quien se afilia y tiene una duda: el WhatsApp de TIMU, si está configurado. */
export function Contacto({ texto = '¿Dudas? Escríbenos por WhatsApp' }: { texto?: string }) {
  const contacto = useContactoRegistro()
  if (!contacto.data?.whatsapp) return null
  return (
    <p className="registro-nota">
      <a className="registro-whatsapp" href={enlaceWhatsApp(contacto.data.whatsapp)} target="_blank" rel="noreferrer">
        <Icono nombre="mensaje" size={14} /> {texto}
      </a>
    </p>
  )
}
