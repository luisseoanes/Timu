import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { ClinicaPage } from './ClinicaPage'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { FamiliaRead, RespuestaRead, SolicitudVirtualRead } from '@/types'

const API = '*/api/v1'
const LUNA = FAMILIA.mascotas![0]!
const OTRO_MEDICO = '99999999-9999-9999-9999-999999999999'
const comoMedico = http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'medico' }))

const solicitud = (cambios: Partial<SolicitudVirtualRead>): SolicitudVirtualRead => ({
  id: 'v1',
  familia_id: FAMILIA.id,
  mascota_id: LUNA.id,
  canal: 'whatsapp',
  motivo: 'Vomitó dos veces',
  estado: 'en_espera',
  prioridad: 'alta',
  asignada_a_id: null,
  respuesta: null,
  historia_id: null,
  borrador_ia: null,
  created_at: '2026-10-24T13:00:00Z',
  ...cambios,
})

const RESPUESTA: RespuestaRead = {
  codigo: 'ayuno',
  titulo: 'Ayuno y observación',
  cuerpo: 'Deja a {{1}} en ayuno {{2}} horas.',
  variables: ['mascota', 'horas'],
  estado: 'aprobada',
}

function conCola(...cola: SolicitudVirtualRead[]) {
  server.use(
    http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
    http.get(`${API}/clinica/virtual/cola`, () => HttpResponse.json(cola)),
    http.get(`${API}/clinica/respuestas-virtuales`, () => HttpResponse.json([RESPUESTA])),
  )
}

async function abrirPestana(nombre: string) {
  const user = userEvent.setup()
  renderizar(<ClinicaPage />)
  await user.click(await screen.findByRole('tab', { name: nombre }))
  return user
}

async function elegirFamilia(user: ReturnType<typeof userEvent.setup>, contenedor: HTMLElement) {
  await user.type(within(contenedor).getByRole('searchbox'), 'Ana')
  await user.click(await within(contenedor).findByRole('button', { name: /ana ruiz/i }))
}

describe('historia clínica', () => {
  it('lista las mascotas de la familia elegida, también las dadas de baja', async () => {
    const familia: FamiliaRead = {
      ...FAMILIA,
      mascotas: [LUNA, { ...LUNA, id: 'm2', nombre: 'Tom', especie: 'gato', activa: false }],
    }
    server.use(http.get(`${API}/familias`, () => HttpResponse.json({ items: [familia], total: 1, limit: 6, offset: 0 })))
    const user = userEvent.setup()
    renderizar(<ClinicaPage />)
    await elegirFamilia(user, document.body)
    expect(await screen.findByRole('link', { name: /luna/i })).toHaveAttribute('href', `/clinica/mascotas/${LUNA.id}`)
    expect(screen.getByRole('link', { name: /tom/i })).toHaveTextContent('De baja')
  })
})

describe('cola de atención virtual', () => {
  it('un médico toma una solicitud libre; las de otros no las atiende', async () => {
    let tomada = false
    server.use(
      comoMedico,
      http.post(`${API}/clinica/virtual/v1/toma`, () => {
        tomada = true
        return HttpResponse.json(solicitud({ asignada_a_id: USUARIO_ADMIN.id }))
      }),
    )
    conCola(
      solicitud({ id: 'v1', borrador_ia: { borrador: 'x', senales_alarma: [], recomendar_presencial: false } }),
      solicitud({ id: 'v2', motivo: 'Cojea', asignada_a_id: OTRO_MEDICO }),
    )
    const user = await abrirPestana('Atención virtual')
    const fila = (motivo: string) => screen.getByText(motivo).closest('tr')!
    await screen.findByText('Vomitó dos veces')
    expect(within(fila('Vomitó dos veces')).getByText('Borrador IA')).toBeInTheDocument()
    await waitFor(() => expect(within(fila('Vomitó dos veces')).getByText('Luna')).toBeInTheDocument())
    expect(within(fila('Cojea')).queryByRole('button', { name: 'Tomar' })).not.toBeInTheDocument()
    expect(within(fila('Cojea')).queryByRole('button', { name: 'Atender' })).not.toBeInTheDocument()
    await user.click(within(fila('Vomitó dos veces')).getByRole('button', { name: 'Tomar' }))
    await waitFor(() => expect(tomada).toBe(true))
  })

  it('avisa si otro médico tomó la solicitud primero', async () => {
    server.use(
      comoMedico,
      http.post(`${API}/clinica/virtual/v1/toma`, () =>
        HttpResponse.json({ detail: 'La solicitud ya fue tomada' }, { status: 409 }),
      ),
    )
    conCola(solicitud({}))
    const user = await abrirPestana('Atención virtual')
    await user.click(await screen.findByRole('button', { name: 'Tomar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('La solicitud ya fue tomada')
  })

  it('la administración atiende cualquiera, pero no la toma ni responde', async () => {
    conCola(solicitud({ asignada_a_id: OTRO_MEDICO }))
    const user = await abrirPestana('Atención virtual')
    expect(screen.queryByRole('button', { name: 'Tomar' })).not.toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Atender' }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).queryByRole('button', { name: 'Enviar respuesta' })).not.toBeInTheDocument()
    expect(within(modal).queryByRole('button', { name: 'Pedir borrador a la IA' })).not.toBeInTheDocument()
  })

  it('muestra la cola vacía', async () => {
    conCola()
    await abrirPestana('Atención virtual')
    expect(await screen.findByText('No hay solicitudes en espera.')).toBeInTheDocument()
  })

  it('explica por qué no cargó la cola', async () => {
    server.use(http.get(`${API}/clinica/virtual/cola`, () => HttpResponse.json({ detail: 'Sin conexión' }, { status: 503 })))
    await abrirPestana('Atención virtual')
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar la cola. Sin conexión')
  })
})

describe('atender una solicitud', () => {
  async function atender(s: SolicitudVirtualRead) {
    server.use(comoMedico)
    conCola(s)
    const user = await abrirPestana('Atención virtual')
    await user.click(await screen.findByRole('button', { name: 'Atender' }))
    return { user, modal: await screen.findByRole('dialog') }
  }

  it('pide el borrador a la IA y avisa de que llega en segundos', async () => {
    let pedido = false
    server.use(
      http.post(`${API}/clinica/virtual/v1/borrador`, () => {
        pedido = true
        return HttpResponse.json({}, { status: 202 })
      }),
    )
    const { user, modal } = await atender(solicitud({ asignada_a_id: USUARIO_ADMIN.id }))
    await user.click(within(modal).getByRole('button', { name: 'Pedir borrador a la IA' }))
    expect(await within(modal).findByText(/Llega en unos segundos/)).toBeInTheDocument()
    expect(pedido).toBe(true)
  })

  it('explica por qué no se pudo pedir el borrador', async () => {
    server.use(
      http.post(`${API}/clinica/virtual/v1/borrador`, () => HttpResponse.json({ detail: 'IA desactivada' }, { status: 409 })),
    )
    const { user, modal } = await atender(solicitud({ asignada_a_id: USUARIO_ADMIN.id }))
    await user.click(within(modal).getByRole('button', { name: 'Pedir borrador a la IA' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('IA desactivada')
  })

  it('el borrador destaca las señales de alarma y la recomendación presencial', async () => {
    const { modal } = await atender(
      solicitud({
        asignada_a_id: USUARIO_ADMIN.id,
        borrador_ia: { borrador: 'Ayuno de 6 horas.', senales_alarma: ['sangre', 'letargo'], recomendar_presencial: true },
      }),
    )
    expect(within(modal).getByText('Señales de alarma: sangre, letargo')).toBeInTheDocument()
    expect(within(modal).getByText('La IA sugiere una valoración presencial.')).toBeInTheDocument()
  })

  it('responde con las variables y el diagnóstico para la historia', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/clinica/virtual/v1/respuesta`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({})
      }),
    )
    const { user, modal } = await atender(solicitud({ asignada_a_id: USUARIO_ADMIN.id }))
    await waitFor(() => expect(within(modal).getByRole('option', { name: RESPUESTA.titulo })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Respuesta aprobada'), 'ayuno')
    expect(within(modal).getByText('Deja a [mascota] en ayuno [horas] horas.')).toBeInTheDocument()
    await user.type(within(modal).getByLabelText('mascota'), 'Luna')
    await user.type(within(modal).getByLabelText('horas'), '6')
    await user.type(within(modal).getByLabelText('Diagnóstico para la historia (opcional)'), ' Gastritis ')
    expect(within(modal).getByText('Deja a Luna en ayuno 6 horas.')).toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Enviar respuesta' }))
    await waitFor(() =>
      expect(enviado).toEqual({ respuesta_codigo: 'ayuno', variables: ['Luna', '6'], diagnostico: 'Gastritis' }),
    )
  })

  it('explica por qué no se pudo responder', async () => {
    server.use(
      http.post(`${API}/clinica/virtual/v1/respuesta`, () =>
        HttpResponse.json({ detail: 'La respuesta ya no está aprobada' }, { status: 409 }),
      ),
    )
    const { user, modal } = await atender(solicitud({ asignada_a_id: USUARIO_ADMIN.id }))
    await waitFor(() => expect(within(modal).getByRole('option', { name: RESPUESTA.titulo })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Respuesta aprobada'), 'ayuno')
    await user.type(within(modal).getByLabelText('mascota'), 'Luna')
    await user.type(within(modal).getByLabelText('horas'), '6')
    await user.click(within(modal).getByRole('button', { name: 'Enviar respuesta' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('La respuesta ya no está aprobada')
  })

  it('una respondida muestra la respuesta, enlaza la historia y se cierra', async () => {
    let cerrada = false
    server.use(
      http.post(`${API}/clinica/virtual/v1/cierre`, () => {
        cerrada = true
        return HttpResponse.json(solicitud({ estado: 'cerrada' }))
      }),
    )
    const { user, modal } = await atender(
      solicitud({ asignada_a_id: USUARIO_ADMIN.id, respuesta: 'Ayuno de 6 horas', historia_id: 'h9' }),
    )
    expect(within(modal).getByRole('status')).toHaveTextContent('Respondida: Ayuno de 6 horas')
    expect(within(modal).getByRole('link', { name: 'Ver en la historia' })).toHaveAttribute('href', '/clinica/historias/h9')
    await user.click(within(modal).getByRole('button', { name: 'Cerrar solicitud' }))
    await waitFor(() => expect(cerrada).toBe(true))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo cerrar', async () => {
    server.use(http.post(`${API}/clinica/virtual/v1/cierre`, () => HttpResponse.json({ detail: 'Ya estaba cerrada' }, { status: 409 })))
    const { user, modal } = await atender(solicitud({ asignada_a_id: USUARIO_ADMIN.id, respuesta: 'Listo' }))
    await user.click(within(modal).getByRole('button', { name: 'Cerrar solicitud' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya estaba cerrada')
  })
})

describe('registrar una solicitud', () => {
  it('registra la consulta telefónica con solo las mascotas activas', async () => {
    let enviado: unknown = null
    const familia: FamiliaRead = { ...FAMILIA, mascotas: [LUNA, { ...LUNA, id: 'm2', nombre: 'Tom', activa: false }] }
    server.use(
      http.get(`${API}/familias`, () => HttpResponse.json({ items: [familia], total: 1, limit: 6, offset: 0 })),
      http.post(`${API}/clinica/virtual`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(solicitud({}), { status: 201 })
      }),
    )
    conCola()
    const user = await abrirPestana('Atención virtual')
    await user.click(screen.getByRole('button', { name: /registrar solicitud/i }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByRole('button', { name: 'Registrar' })).toBeDisabled()
    await elegirFamilia(user, modal)
    expect(within(modal).queryByRole('option', { name: 'Tom' })).not.toBeInTheDocument()
    await user.selectOptions(within(modal).getByLabelText('Prioridad'), 'alta')
    await user.type(within(modal).getByLabelText('Motivo de la consulta'), ' No quiere comer ')
    await user.click(within(modal).getByRole('button', { name: 'Registrar' }))
    await waitFor(() =>
      expect(enviado).toEqual({ mascota_id: LUNA.id, motivo: 'No quiere comer', prioridad: 'alta', canal: 'panel' }),
    )
  })

  it('explica por qué no se pudo registrar', async () => {
    server.use(
      http.post(`${API}/clinica/virtual`, () => HttpResponse.json({ detail: 'La mascota no tiene plan vigente' }, { status: 409 })),
    )
    conCola()
    const user = await abrirPestana('Atención virtual')
    await user.click(screen.getByRole('button', { name: /registrar solicitud/i }))
    const modal = await screen.findByRole('dialog')
    await elegirFamilia(user, modal)
    await user.type(within(modal).getByLabelText('Motivo de la consulta'), 'No quiere comer')
    await user.click(within(modal).getByRole('button', { name: 'Registrar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('La mascota no tiene plan vigente')
  })
})

describe('respuestas aprobadas', () => {
  it('la administración aprueba las que esperan', async () => {
    let aprobada = ''
    server.use(
      http.get(`${API}/clinica/respuestas-virtuales`, () =>
        HttpResponse.json([RESPUESTA, { ...RESPUESTA, codigo: 'hidratar', titulo: 'Hidratación', estado: 'borrador' }]),
      ),
      http.post(`${API}/clinica/respuestas-virtuales/:codigo/aprobacion`, ({ params }) => {
        aprobada = String(params.codigo)
        return HttpResponse.json({ ...RESPUESTA, codigo: 'hidratar' })
      }),
    )
    const user = await abrirPestana('Respuestas aprobadas')
    expect(await screen.findByText('Aprobada')).toBeInTheDocument()
    expect(screen.getByText('Por aprobar')).toBeInTheDocument()
    const aprobar = screen.getAllByRole('button', { name: 'Aprobar' })
    expect(aprobar).toHaveLength(1)
    await user.click(aprobar[0]!)
    await waitFor(() => expect(aprobada).toBe('hidratar'))
  })

  it('explica por qué no se pudo aprobar', async () => {
    server.use(
      http.get(`${API}/clinica/respuestas-virtuales`, () => HttpResponse.json([{ ...RESPUESTA, estado: 'borrador' }])),
      http.post(`${API}/clinica/respuestas-virtuales/:codigo/aprobacion`, () =>
        HttpResponse.json({ detail: 'Solo la administración aprueba' }, { status: 403 }),
      ),
    )
    const user = await abrirPestana('Respuestas aprobadas')
    await user.click(await screen.findByRole('button', { name: 'Aprobar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Solo la administración aprueba')
  })

  it('un médico ve las pendientes pero no las aprueba', async () => {
    server.use(
      comoMedico,
      http.get(`${API}/clinica/respuestas-virtuales`, () => HttpResponse.json([{ ...RESPUESTA, estado: 'borrador' }])),
    )
    await abrirPestana('Respuestas aprobadas')
    expect(await screen.findByText('Por aprobar')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Aprobar' })).not.toBeInTheDocument()
  })

  it('crea una respuesta con sus variables en orden', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/clinica/respuestas-virtuales`, () => HttpResponse.json([])),
      http.post(`${API}/clinica/respuestas-virtuales`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(RESPUESTA, { status: 201 })
      }),
    )
    const user = await abrirPestana('Respuestas aprobadas')
    expect(await screen.findByText('Aún no hay respuestas. Crea la primera.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /nueva respuesta/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Código'), 'ayuno')
    await user.type(within(modal).getByLabelText('Título'), ' Ayuno ')
    await user.type(within(modal).getByLabelText(/^Texto/), 'Deja a {{{{1}} en ayuno')
    await user.type(within(modal).getByLabelText(/Nombre de cada variable/), 'mascota, , horas')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() =>
      expect(enviado).toEqual({ codigo: 'ayuno', titulo: 'Ayuno', cuerpo: 'Deja a {{1}} en ayuno', variables: ['mascota', 'horas'] }),
    )
  })

  it('explica por qué no se pudo guardar la respuesta', async () => {
    server.use(
      http.get(`${API}/clinica/respuestas-virtuales`, () => HttpResponse.json([])),
      http.post(`${API}/clinica/respuestas-virtuales`, () => HttpResponse.json({ detail: 'El código ya existe' }, { status: 409 })),
    )
    const user = await abrirPestana('Respuestas aprobadas')
    await user.click(await screen.findByRole('button', { name: /nueva respuesta/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Código'), 'ayuno')
    await user.type(within(modal).getByLabelText('Título'), 'Ayuno')
    await user.type(within(modal).getByLabelText(/^Texto/), 'Texto')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('El código ya existe')
  })
})

describe('plantillas de consulta', () => {
  it('lista las plantillas con sus campos prellenados', async () => {
    server.use(
      http.get(`${API}/clinica/plantillas`, () =>
        HttpResponse.json([
          { codigo: 'otitis', nombre: 'Otitis', campos: { motivo: 'Rasca el oído', diagnostico: 'Otitis' } },
          { codigo: 'vacia', nombre: 'Control', campos: {} },
        ]),
      ),
    )
    await abrirPestana('Plantillas de consulta')
    expect(await screen.findByText('motivo, diagnostico')).toBeInTheDocument()
    expect(screen.getByText('Sin campos prellenados')).toBeInTheDocument()
  })

  it('crea una plantilla solo con los campos llenos', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/clinica/plantillas`, () => HttpResponse.json([])),
      http.post(`${API}/clinica/plantillas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ codigo: 'otitis', nombre: 'Otitis', campos: {} }, { status: 201 })
      }),
    )
    const user = await abrirPestana('Plantillas de consulta')
    expect(await screen.findByText(/No hay plantillas/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /nueva plantilla/i }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).queryByLabelText(/Notas internas/)).not.toBeInTheDocument()
    await user.type(within(modal).getByLabelText('Código'), 'otitis')
    await user.type(within(modal).getByLabelText('Nombre'), 'Otitis')
    await user.type(within(modal).getByLabelText('Diagnóstico'), ' Otitis externa ')
    await user.click(within(modal).getByRole('button', { name: 'Guardar plantilla' }))
    await waitFor(() =>
      expect(enviado).toEqual({ codigo: 'otitis', nombre: 'Otitis', campos: { diagnostico: 'Otitis externa' } }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo guardar la plantilla', async () => {
    server.use(
      http.get(`${API}/clinica/plantillas`, () => HttpResponse.json([])),
      http.post(`${API}/clinica/plantillas`, () => HttpResponse.json({ detail: 'El código ya existe' }, { status: 409 })),
    )
    const user = await abrirPestana('Plantillas de consulta')
    await user.click(await screen.findByRole('button', { name: /nueva plantilla/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Código'), 'otitis')
    await user.type(within(modal).getByLabelText('Nombre'), 'Otitis')
    await user.click(within(modal).getByRole('button', { name: 'Guardar plantilla' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('El código ya existe')
  })
})
