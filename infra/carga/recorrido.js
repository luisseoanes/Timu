// Prueba de carga (F4-QAA-02, fase 5 de docs/plan-persistencia.md).
//
// Usuarios simultaneos del equipo y del portal recorren listados, fichas y el dashboard sobre
// el volumen de scripts.datos_volumen. Falla si con ese volumen se superan los tiempos
// acordados: p95 < 500 ms en consultas y < 2 s en el dashboard (F4-DAS-02), con menos del
// 1 % de errores. Entra por la red interna del compose, directo a la API.
//
// Cada usuario virtual es una persona: su propio usuario (los impares, del equipo; los
// pares, del portal), su propia sesion y de 1 a 3 s entre peticiones. Con usuarios
// compartidos y sin pausa se mediria el limite de peticiones por usuario, no la base.
//
// Local (completa): ver "Prueba de carga" en el CLAUDE.md de la raiz.
// CI (reducida): VUS y DURACION mas bajos, en el job del stack.

import http from 'k6/http';
import { check, sleep } from 'k6';

const API = __ENV.API_URL || 'http://api:8000/api/v1';
const COOKIE = 'timu_sesion';
const CLAVE = 'carga12345'; // CLAVE_CARGA de scripts.datos_volumen
const VUS = Number(__ENV.VUS || 20);

export const options = {
  vus: VUS,
  duration: __ENV.DURACION || '5m',
  // El ingreso admite 10 por minuto y por IP: 20 usuarios tardan unos dos minutos en entrar.
  setupTimeout: '10m',
  thresholds: {
    'http_req_duration{tipo:consulta}': ['p(95)<500'],
    'http_req_duration{tipo:dashboard}': ['p(95)<2000'],
    'http_req_failed{tipo:consulta}': ['rate<0.01'],
    'http_req_failed{tipo:dashboard}': ['rate<0.01'],
    checks: ['rate>0.99'],
    // Sin muestras, k6 da por cumplido cualquier umbral: un recorrido que no llegara a hacer
    // peticiones saldria en verde.
    'http_reqs{tipo:consulta}': ['count>0'],
    'http_reqs{tipo:dashboard}': ['count>0'],
  },
};

function ingresar(usuario) {
  for (;;) {
    // Jar propio: con el del usuario virtual, cada ingreso pisaria la cookie del anterior y
    // esa cookie viajaria junto a la cabecera explicita.
    const resp = http.post(`${API}/auth/login`, { username: usuario, password: CLAVE }, {
      tags: { tipo: 'ingreso' },
      jar: new http.CookieJar(),
      responseCallback: http.expectedStatuses(200, 429),
    });
    if (resp.status === 429) {
      sleep(Number(resp.headers['Retry-After'] || 10) + 1);
      continue;
    }
    if (resp.status !== 200) {
      throw new Error(`No se pudo ingresar como ${usuario}: ${resp.status} ${resp.body}`);
    }
    return { Cookie: `${COOKIE}=${resp.cookies[COOKIE][0].value}` };
  }
}

export function setup() {
  const porPerfil = Math.ceil(VUS / 2);
  if (porPerfil > 25) {
    throw new Error('scripts.datos_volumen crea 25 usuarios por perfil: VUS <= 50');
  }
  const numero = (k) => String(k + 1).padStart(2, '0');
  const equipo = [];
  const portal = [];
  for (let k = 0; k < porPerfil; k++) {
    equipo.push(ingresar(`carga-equipo-${numero(k)}@volumen.example.com`));
    portal.push(ingresar(`carga-portal-${numero(k)}@volumen.example.com`));
  }
  const pagina = http.get(`${API}/familias?q=Familia&limit=100`, { headers: equipo[0] });
  const familias = (pagina.json('items') || []).map((f) => f.id);
  if (familias.length === 0) {
    throw new Error(`No hay volumen: ejecuta antes scripts.datos_volumen (${pagina.status})`);
  }
  return { equipo, portal, familias };
}

const hoy = new Date();
const desde = new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1).toISOString().slice(0, 10);
const hasta = new Date(hoy.getFullYear(), hoy.getMonth(), 0).toISOString().slice(0, 10);
const azar = (lista) => lista[Math.floor(Math.random() * lista.length)];

// [peso, tipo, nombre, ruta]: lo que hace cada perfil en un dia normal. El nombre agrupa
// las metricas, porque la ruta concreta cambia en cada peticion.
const PETICIONES = {
  equipo: [
    [4, 'consulta', 'buscar familia', () => `/familias?q=Familia%20${Math.floor(Math.random() * 5000)}`],
    [4, 'consulta', 'ficha de familia', (d) => `/familias/${azar(d.familias)}`],
    [3, 'consulta', 'servicios', () => '/servicios?limit=20'],
    [3, 'consulta', 'tareas', () => '/tareas'],
    [2, 'consulta', 'cartera en mora', () => '/cartera/contratos?solo_mora=true'],
    [1, 'consulta', 'encuestas', () => '/encuestas'],
    [1, 'consulta', 'interesados', () => '/comercial/interesados'],
    [1, 'dashboard', 'dashboard', () => `/dashboard/indicadores?desde=${desde}&hasta=${hasta}`],
  ],
  portal: [
    [1, 'consulta', 'portal: mi familia', () => '/portal/mi-familia'],
    [1, 'consulta', 'portal: estado de cuenta', () => '/portal/estado-cuenta'],
    [1, 'consulta', 'portal: servicios', () => '/portal/servicios'],
  ],
};

function elegir(peticiones) {
  const total = peticiones.reduce((suma, [peso]) => suma + peso, 0);
  let tirada = Math.random() * total;
  for (const peticion of peticiones) {
    tirada -= peticion[0];
    if (tirada <= 0) return peticion;
  }
  return peticiones[0];
}

export default function (datos) {
  const perfil = __VU % 2 === 1 ? 'equipo' : 'portal';
  const sesion = datos[perfil][Math.floor((__VU - 1) / 2)];
  const [, tipo, nombre, ruta] = elegir(PETICIONES[perfil]);
  const resp = http.get(`${API}${ruta(datos)}`, { headers: sesion, tags: { tipo, name: nombre } });
  check(resp, { 'responde 200': (r) => r.status === 200 });
  sleep(1 + Math.random() * 2);
}
