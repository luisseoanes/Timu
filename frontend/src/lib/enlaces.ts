/** Los teléfonos se guardan en E.164 con «+»; WhatsApp los quiere sin él. */
export function enlaceWhatsApp(telefono: string): string {
  return `https://wa.me/${telefono.replace(/\D/g, '')}`
}
