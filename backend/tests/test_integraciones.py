"""Clientes de terceros: Wompi, WhatsApp (Meta), SMTP y Google Maps.

Sin red: `httpx.Client` se sustituye por uno con `MockTransport`, asi que se prueba la
peticion que de verdad se arma (URL, cabeceras, cuerpo) y como se clasifica cada
respuesta. La clasificacion temporal/permanente decide si se reintenta un cobro o un
mensaje: equivocarse es cobrar dos veces o perder una notificacion.
"""

import hashlib
import hmac
import json
import smtplib
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app.core.config import settings
from app.integrations import correo, geocodificacion, mapas, payments, whatsapp

pytestmark = pytest.mark.unit


class Red:
    """Responde en orden lo que se le encola y guarda las peticiones recibidas."""

    def __init__(self) -> None:
        self.peticiones: list[httpx.Request] = []
        self._respuestas: list[httpx.Response | Exception] = []

    def responde(self, *respuestas: httpx.Response | Exception) -> None:
        self._respuestas.extend(respuestas)

    def _manejar(self, peticion: httpx.Request) -> httpx.Response:
        self.peticiones.append(peticion)
        respuesta = self._respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    @property
    def ultima(self) -> httpx.Request:
        return self.peticiones[-1]


@pytest.fixture
def red(monkeypatch) -> Red:
    simulada = Red()
    real = httpx.Client

    def cliente(*args, **kwargs):
        return real(*args, transport=httpx.MockTransport(simulada._manejar), **kwargs)

    monkeypatch.setattr(httpx, "Client", cliente)
    return simulada


def _cuerpo(peticion: httpx.Request) -> dict:
    return json.loads(peticion.content)


def _caida_de_red() -> httpx.ConnectError:
    return httpx.ConnectError("conexion rechazada")


# --- Wompi ------------------------------------------------------------------------------------


@pytest.fixture
def wompi(monkeypatch):
    monkeypatch.setattr(settings, "WOMPI_API_URL", "https://sandbox.wompi.test/v1/")
    monkeypatch.setattr(settings, "WOMPI_PUBLIC_KEY", "pub_test")
    monkeypatch.setattr(settings, "WOMPI_PRIVATE_KEY", "prv_test")
    monkeypatch.setattr(settings, "WOMPI_INTEGRITY_SECRET", "integridad")
    monkeypatch.setattr(settings, "WOMPI_EVENTS_SECRET", "eventos")
    return payments.ClienteWompi()


def _evento_firmado(secreto: str) -> dict:
    datos = {"transaction": {"id": "tx-1", "status": "APPROVED", "amount_in_cents": 4500000}}
    propiedades = ["transaction.id", "transaction.status", "transaction.amount_in_cents"]
    cadena = "tx-1APPROVED4500000" + "1700000000" + secreto
    return {
        "data": datos,
        "timestamp": 1700000000,
        "signature": {
            "properties": propiedades,
            "checksum": hashlib.sha256(cadena.encode()).hexdigest().upper(),
        },
    }


def test_evento_wompi_con_checksum_valido(wompi):
    assert payments.verificar_evento_wompi(_evento_firmado("eventos"))


def test_evento_wompi_alterado_o_firmado_con_otro_secreto(wompi):
    alterado = _evento_firmado("eventos")
    alterado["data"]["transaction"]["amount_in_cents"] = 100
    assert not payments.verificar_evento_wompi(alterado)
    assert not payments.verificar_evento_wompi(_evento_firmado("otro"))
    assert not payments.verificar_evento_wompi({"data": {}})


def test_sin_secreto_de_eventos_solo_se_acepta_fuera_de_produccion(monkeypatch):
    monkeypatch.setattr(settings, "WOMPI_EVENTS_SECRET", "")
    assert payments.verificar_evento_wompi({"data": {}})
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert not payments.verificar_evento_wompi({"data": {}})


def test_link_de_pago_firmado_con_integridad(wompi):
    url = payments.construir_link_pago(
        "AF-1", 4500000, email="ana@correo.co", redireccion="https://timu.co/gracias"
    )
    params = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
    esperado = hashlib.sha256(b"AF-14500000COPintegridad").hexdigest()
    assert url.startswith("https://checkout.wompi.co/p/?")
    assert params == {
        "public-key": "pub_test",
        "currency": "COP",
        "amount-in-cents": "4500000",
        "reference": "AF-1",
        "signature:integrity": esperado,
        "customer-data:email": "ana@correo.co",
        "redirect-url": "https://timu.co/gracias",
    }
    sin_opcionales = parse_qs(urlparse(payments.construir_link_pago("AF-2", 100)).query)
    assert "customer-data:email" not in sin_opcionales
    assert "redirect-url" not in sin_opcionales


def test_token_de_aceptacion_con_la_llave_publica(wompi, red):
    red.responde(
        httpx.Response(
            200, json={"data": {"presigned_acceptance": {"acceptance_token": "acept-1"}}}
        )
    )
    assert wompi.token_aceptacion() == "acept-1"
    assert red.ultima.method == "GET"
    assert str(red.ultima.url) == "https://sandbox.wompi.test/v1/merchants/pub_test"
    assert red.ultima.headers["Authorization"] == "Bearer pub_test"


def test_crear_fuente_de_pago_con_la_llave_privada(wompi, red):
    red.responde(httpx.Response(201, json={"data": {"id": 7788}}))
    assert wompi.crear_fuente_pago("tok_tarjeta", "ana@correo.co", "acept-1") == "7788"
    assert str(red.ultima.url).endswith("/payment_sources")
    assert red.ultima.headers["Authorization"] == "Bearer prv_test"
    assert _cuerpo(red.ultima) == {
        "type": "CARD",
        "token": "tok_tarjeta",
        "customer_email": "ana@correo.co",
        "acceptance_token": "acept-1",
    }


def test_cobro_recurrente_firmado_sobre_la_fuente(wompi, red):
    red.responde(httpx.Response(201, json={"data": {"id": "tx-9", "status": "PENDING"}}))
    respuesta = wompi.cobrar_fuente(
        referencia="CU-1", valor_centavos=4500000, email="ana@correo.co", fuente_id="7788"
    )
    assert respuesta == {"id": "tx-9", "status": "PENDING"}
    cuerpo = _cuerpo(red.ultima)
    assert cuerpo["payment_source_id"] == 7788, "Wompi exige el id numerico"
    assert cuerpo["recurrent"] is True
    assert cuerpo["amount_in_cents"] == 4500000
    assert cuerpo["signature"] == hashlib.sha256(b"CU-14500000COPintegridad").hexdigest()
    assert red.ultima.headers["Authorization"] == "Bearer prv_test"


def test_cobro_con_fuente_no_numerica_se_envia_tal_cual(wompi, red):
    red.responde(httpx.Response(201, json={"data": {"id": "tx-10"}}))
    wompi.cobrar_fuente(referencia="CU-2", valor_centavos=100, email="a@b.co", fuente_id="ps_x")
    assert _cuerpo(red.ultima)["payment_source_id"] == "ps_x"


def test_consultar_transaccion(wompi, red):
    red.responde(httpx.Response(200, json={"data": {"id": "tx-9", "status": "APPROVED"}}))
    assert wompi.consultar_transaccion("tx-9")["status"] == "APPROVED"
    assert str(red.ultima.url).endswith("/transactions/tx-9")
    assert red.ultima.headers["Authorization"] == "Bearer pub_test"


@pytest.mark.parametrize(
    ("respuesta", "temporal"),
    [
        (httpx.Response(503), True),
        (httpx.Response(500), True),
        (httpx.Response(429), True),
        (_caida_de_red(), True),
        (httpx.Response(422, text="tarjeta rechazada"), False),
        (httpx.Response(401), False),
    ],
)
def test_wompi_clasifica_los_errores_para_saber_si_reintentar(wompi, red, respuesta, temporal):
    red.responde(respuesta)
    with pytest.raises(payments.ErrorPasarela) as error:
        wompi.consultar_transaccion("tx-1")
    assert error.value.temporal is temporal


def test_el_rechazo_de_wompi_conserva_el_motivo(wompi, red):
    red.responde(httpx.Response(422, text="CARD_DECLINED: fondos insuficientes"))
    with pytest.raises(payments.ErrorPasarela, match="fondos insuficientes"):
        wompi.consultar_transaccion("tx-1")


# --- WhatsApp ---------------------------------------------------------------------------------


@pytest.fixture
def wa(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_ACCESS_TOKEN", "token-meta")
    monkeypatch.setattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "12345")
    monkeypatch.setattr(settings, "WHATSAPP_API_VERSION", "v21.0")
    return whatsapp.WhatsAppClient()


def _wamid(id_: str = "wamid.1") -> httpx.Response:
    return httpx.Response(200, json={"messages": [{"id": id_}]})


def test_firma_de_meta(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "secreto-app")
    cuerpo = b'{"entry": []}'
    firma = "sha256=" + hmac.new(b"secreto-app", cuerpo, hashlib.sha256).hexdigest()
    assert whatsapp.verificar_firma(cuerpo, firma)
    assert not whatsapp.verificar_firma(cuerpo + b" ", firma)
    assert not whatsapp.verificar_firma(cuerpo, "sha256=otra")


def test_sin_secreto_de_meta_solo_se_acepta_fuera_de_produccion(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "")
    assert whatsapp.verificar_firma(b"{}", "")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert not whatsapp.verificar_firma(b"{}", "")


def test_sin_credenciales_no_sale_nada(monkeypatch, red):
    monkeypatch.setattr(settings, "WHATSAPP_ACCESS_TOKEN", "")
    cliente = whatsapp.WhatsAppClient()
    assert not cliente.configurado
    assert cliente.enviar_texto("573001112233", "hola") == "no_configurado"
    assert red.peticiones == []


def test_enviar_texto(wa, red):
    red.responde(_wamid("wamid.texto"))
    assert wa.enviar_texto("573001112233", "Su servicio va en camino") == "wamid.texto"
    assert str(red.ultima.url) == "https://graph.facebook.com/v21.0/12345/messages"
    assert red.ultima.headers["Authorization"] == "Bearer token-meta"
    assert _cuerpo(red.ultima) == {
        "messaging_product": "whatsapp",
        "to": "573001112233",
        "type": "text",
        "text": {"body": "Su servicio va en camino"},
    }


def test_enviar_plantilla_con_parametros(wa, red):
    red.responde(_wamid())
    wa.enviar_plantilla("573001112233", "recordatorio_cuota", ["Ana", "45.000"])
    plantilla = _cuerpo(red.ultima)["template"]
    assert plantilla["name"] == "recordatorio_cuota"
    assert plantilla["language"] == {"code": "es"}
    assert plantilla["components"] == [
        {
            "type": "body",
            "parameters": [{"type": "text", "text": "Ana"}, {"type": "text", "text": "45.000"}],
        }
    ]


def test_enviar_plantilla_sin_parametros(wa, red):
    red.responde(_wamid())
    wa.enviar_plantilla("573001112233", "bienvenida", idioma="es_CO")
    plantilla = _cuerpo(red.ultima)["template"]
    assert plantilla["components"] == []
    assert plantilla["language"] == {"code": "es_CO"}


@pytest.mark.parametrize(
    ("respuesta", "temporal"),
    [
        (httpx.Response(429), True),
        (httpx.Response(502), True),
        (_caida_de_red(), True),
        (httpx.Response(400, text="numero invalido"), False),
    ],
)
def test_whatsapp_clasifica_los_errores_para_saber_si_reintentar(wa, red, respuesta, temporal):
    red.responde(respuesta)
    with pytest.raises(whatsapp.ErrorWhatsApp) as error:
        wa.enviar_texto("573001112233", "hola")
    assert error.value.temporal is temporal


# --- Correo -----------------------------------------------------------------------------------


class SmtpFalso:
    """Sustituye a smtplib.SMTP: registra la conversacion y puede fallar a demanda."""

    instancias: list["SmtpFalso"] = []
    fallo: Exception | None = None

    def __init__(self, host, puerto, timeout):
        self.conexion = (host, puerto, timeout)
        self.pasos: list[str] = []
        self.enviado = None
        SmtpFalso.instancias.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.pasos.append("starttls")

    def login(self, usuario, clave):
        self.pasos.append(f"login:{usuario}:{clave}")

    def send_message(self, mensaje):
        if SmtpFalso.fallo:
            raise SmtpFalso.fallo
        self.enviado = mensaje


@pytest.fixture
def smtp(monkeypatch):
    SmtpFalso.instancias, SmtpFalso.fallo = [], None
    monkeypatch.setattr(smtplib, "SMTP", SmtpFalso)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.timu.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_FROM", "TIMU <no-responder@timu.co>")
    return SmtpFalso


def test_correo_sin_servidor_no_se_envia(monkeypatch, smtp):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    assert correo.enviar("ana@correo.co", "Asunto", "Cuerpo") == "no_configurado"
    assert smtp.instancias == []


def test_correo_con_tls_y_adjunto(smtp):
    pdf = b"%PDF-1.4 contrato"
    assert (
        correo.enviar(
            "ana@correo.co",
            "Su contrato",
            "Adjuntamos el contrato.",
            [("c.pdf", pdf, "application/pdf")],
        )
        == "enviado"
    )
    (sesion,) = smtp.instancias
    assert sesion.conexion == ("smtp.timu.test", 587, 15)
    assert sesion.pasos == ["starttls"], "sin usuario no se autentica"
    mensaje = sesion.enviado
    assert (mensaje["To"], mensaje["Subject"]) == ("ana@correo.co", "Su contrato")
    assert mensaje["From"] == "TIMU <no-responder@timu.co>"
    (adjunto,) = list(mensaje.iter_attachments())
    assert adjunto.get_filename() == "c.pdf"
    assert adjunto.get_content_type() == "application/pdf"
    assert adjunto.get_content() == pdf


def test_correo_se_autentica_si_hay_usuario(monkeypatch, smtp):
    monkeypatch.setattr(settings, "SMTP_USER", "envios")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "clave")
    correo.enviar("ana@correo.co", "Asunto", "Cuerpo")
    assert smtp.instancias[0].pasos == ["starttls", "login:envios:clave"]


@pytest.mark.parametrize(
    ("fallo", "temporal"),
    [
        (smtplib.SMTPRecipientsRefused({"ana@correo.co": (550, b"no existe")}), False),
        (smtplib.SMTPServerDisconnected("se cayo"), True),
        (ConnectionRefusedError("sin servidor"), True),
    ],
)
def test_correo_clasifica_los_errores_para_saber_si_reintentar(smtp, fallo, temporal):
    smtp.fallo = fallo
    with pytest.raises(correo.ErrorCorreo) as error:
        correo.enviar("ana@correo.co", "Asunto", "Cuerpo")
    assert error.value.temporal is temporal


# --- Google Maps ------------------------------------------------------------------------------


@pytest.fixture
def maps_key(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_MAPS_API_KEY", "clave-maps")


def _matriz(*filas: list[dict], status: str = "OK") -> httpx.Response:
    return httpx.Response(200, json={"status": status, "rows": [{"elements": f} for f in filas]})


def _ok(metros: int, segundos: int) -> dict:
    return {"status": "OK", "distance": {"value": metros}, "duration": {"value": segundos}}


def test_distance_matrix_devuelve_metros_y_segundos_por_par(maps_key, red):
    red.responde(_matriz([_ok(1200, 300), {"status": "ZERO_RESULTS"}]))
    assert mapas.configurado()
    resultado = mapas.consultar([(4.6, -74.08)], [(4.65, -74.05), (4.7, -74.1)])
    assert resultado == [[(1200, 300), None]]
    params = red.ultima.url.params
    assert params["origins"] == "4.600000,-74.080000"
    assert params["destinations"] == "4.650000,-74.050000|4.700000,-74.100000"
    assert (params["mode"], params["units"], params["key"]) == ("driving", "metric", "clave-maps")


def test_distance_matrix_rechaza_consultas_por_encima_del_limite(maps_key, red):
    with pytest.raises(ValueError):
        mapas.consultar([(4.6, -74.0)] * 11, [(4.6, -74.0)] * 10)
    with pytest.raises(ValueError):
        mapas.consultar([(4.6, -74.0)] * 26, [(4.6, -74.0)])
    assert red.peticiones == [], "no se paga una consulta que Google iba a rechazar"


@pytest.mark.parametrize(
    "respuesta",
    [
        _matriz(status="OVER_QUERY_LIMIT"),
        _caida_de_red(),
        httpx.Response(200, text="<html>no es json</html>"),
    ],
)
def test_distance_matrix_no_disponible(maps_key, red, respuesta):
    red.responde(respuesta)
    with pytest.raises(mapas.ErrorMapas):
        mapas.consultar([(4.6, -74.0)], [(4.7, -74.1)])


def _geocodigo(*tipos: str, status: str = "OK", lat=4.65, lng=-74.05) -> httpx.Response:
    resultados = [{"types": list(tipos), "geometry": {"location": {"lat": lat, "lng": lng}}}]
    return httpx.Response(200, json={"status": status, "results": resultados})


def test_geocodificar_una_direccion_precisa(maps_key, red):
    red.responde(_geocodigo("street_address"))
    assert geocodificacion.geocodificar("Cra 7 # 72-41", "Bogota") == (4.65, -74.05)
    params = red.ultima.url.params
    assert params["address"] == "Cra 7 # 72-41, Bogota, Colombia"
    assert (params["region"], params["components"]) == ("co", "country:CO")


def test_geocodificar_sin_clave_no_consulta(monkeypatch, red):
    monkeypatch.setattr(settings, "GOOGLE_MAPS_API_KEY", "")
    assert geocodificacion.geocodificar("Cra 7 # 72-41", "Bogota") is None
    assert red.peticiones == []


@pytest.mark.parametrize(
    "respuesta",
    [
        _geocodigo("locality", "political"),  # solo ubica la ciudad: no sirve para la ruta
        _geocodigo(status="ZERO_RESULTS"),
        httpx.Response(200, json={"status": "OK", "results": []}),
        _caida_de_red(),
        httpx.Response(200, text="no es json"),
    ],
)
def test_geocodificar_descarta_lo_impreciso_o_no_disponible(maps_key, red, respuesta):
    red.responde(respuesta)
    assert geocodificacion.geocodificar("Calle falsa 123", "Bogota") is None
