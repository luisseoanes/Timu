"""Volumen sintetico para las pruebas de carga (F4-QAA-02, fase 5 de docs/plan-persistencia.md).

Genera el volumen proyectado a 12 meses: 5.000 familias con sus mascotas, contratos, un ano
de cuotas, pagos aplicados, servicios, mensajes y tareas. La bitacora sale sola, de los
triggers de auditoria. `--escala` lo reduce o lo amplia (el CI usa 0.1).

Crea ademas los usuarios de la prueba de carga (infra/carga/recorrido.js), uno por usuario
virtual: el limite de peticiones es por usuario, y 20 personas no comparten una sesion.
`carga-equipo-NN@volumen.example.com` (comercial) y `carga-portal-NN@volumen.example.com`,
titular de la familia NN del volumen, todos con la clave CLAVE_CARGA. El dominio no puede
ser `.test` ni otro reservado: la API valida el email al responder y daria un 500.

Escribe por SQL como dueno del esquema, con generate_series: es la unica forma de cargar este
volumen en segundos. Las restricciones, los catalogos y los triggers de la base se aplican
igual, asi que lo que genera es tan coherente como lo que escribiria la aplicacion. Solo
para desarrollo, pruebas y CI: se niega en un ambiente desplegado. Si el volumen ya existe,
no hace nada.

Uso: docker compose exec api python -m scripts.datos_volumen [--escala 0.1]
"""

import argparse
import time

from sqlalchemy import create_engine, text

from app.core.config import settings
from app.core.security import hash_password

FAMILIAS = 5_000
USUARIOS_CARGA = 25  # por perfil: admite hasta 50 usuarios virtuales
CLAVE_CARGA = "carga12345"
_MARCA = "VOL"

# Cada paso es una sentencia; :n es el numero de familias de la escala elegida.
_PASOS: list[tuple[str, str]] = [
    (
        "familias",
        """
        INSERT INTO familias (titular_nombre, tipo_documento, documento, telefono, email,
            ciudad, estado, origen, dada_de_baja_en)
        SELECT 'Familia ' || g, 'CC', 'VOL' || lpad(g::text, 9, '0'),
            '+57300' || lpad(g::text, 7, '0'), 'familia' || g || '@volumen.example.com',
            (SELECT array_agg(nombre ORDER BY nombre) FROM ciudades WHERE activa)
                [1 + g % (SELECT count(*) FROM ciudades WHERE activa)],
            CASE WHEN g % 33 = 0 THEN 'cancelada'::estado_afiliacion
                 WHEN g % 14 = 0 THEN 'en_mora' ELSE 'activa' END,
            'panel',
            CASE WHEN g % 33 = 0 THEN now() - interval '20 days' END
        FROM generate_series(1, :n) AS g
        """,
    ),
    (
        "mascotas",
        """
        INSERT INTO mascotas (familia_id, nombre, especie, activa, fecha_nacimiento)
        SELECT f.id, 'Mascota ' || k, CASE WHEN k = 2 THEN 'felino' ELSE 'canino' END, true,
            current_date - (365 + (random() * 3000)::int)
        FROM familias f
        CROSS JOIN LATERAL generate_series(1, 1 + (f.documento::text ~ '[13579]$')::int) AS k
        WHERE f.documento LIKE 'VOL%'
        """,
    ),
    (
        "contratos",
        """
        INSERT INTO contratos (familia_id, plan_id, numero, fecha_inicio, fecha_renovacion,
            fecha_fin, valor_mensual, valor_plan, dia_corte, estado, mascotas_adicionales,
            valor_adicional_mascota, saldo_a_favor, evidencia_aceptacion)
        SELECT f.id, p.id, 'VOL-' || substr(f.documento, 4), inicio, inicio + interval '1 year',
            CASE WHEN f.estado = 'cancelada' THEN current_date - 20 END,
            p.valor_mensual, p.valor_mensual, 1 + extract(day FROM inicio)::int % 28,
            f.estado, 0, 0, 0, '{}'
        FROM familias f
        CROSS JOIN LATERAL (SELECT current_date - interval '1 year'
                                   + ((random() * 25)::int || ' days')::interval AS inicio) i
        CROSS JOIN LATERAL (SELECT id, valor_mensual FROM planes WHERE codigo = 'individual') p
        WHERE f.documento LIKE 'VOL%'
        """,
    ),
    (
        "cuotas",
        """
        INSERT INTO cuotas (contrato_id, periodo, fecha_vencimiento, valor, valor_pagado,
            estado, dias_mora, tipo)
        SELECT c.id, to_char(venc, 'YYYY-MM'), venc, c.valor_mensual,
            CASE WHEN pendiente THEN 0 ELSE c.valor_mensual END,
            CASE WHEN pendiente THEN 'pendiente'::estado_cuota ELSE 'pagada' END,
            CASE WHEN pendiente THEN greatest(current_date - venc, 0) ELSE 0 END, 'mensual'
        FROM contratos c
        CROSS JOIN LATERAL generate_series(0, 11) AS m
        CROSS JOIN LATERAL (SELECT (c.fecha_inicio + (m || ' months')::interval)::date AS venc) v
        CROSS JOIN LATERAL (SELECT c.estado = 'en_mora' AND m >= 10 AS pendiente) e
        WHERE c.numero LIKE 'VOL-%' AND v.venc <= current_date + 30
        """,
    ),
    (
        "pagos",
        """
        INSERT INTO pagos (familia_id, contrato_id, referencia_externa, proveedor, medio,
            valor, estado, aplicado, fecha_pago)
        SELECT c.familia_id, c.id, 'VOL-' || q.id, 'manual', 'transferencia', q.valor,
            'aprobado', true, q.fecha_vencimiento - 2
        FROM cuotas q JOIN contratos c ON c.id = q.contrato_id
        WHERE c.numero LIKE 'VOL-%' AND q.estado = 'pagada'
        """,
    ),
    (
        "aplicaciones_pago",
        """
        INSERT INTO aplicaciones_pago (pago_id, cuota_id, valor)
        SELECT p.id, q.id, q.valor
        FROM pagos p JOIN cuotas q ON p.referencia_externa = 'VOL-' || q.id
        """,
    ),
    (
        "servicios",
        """
        INSERT INTO servicios (familia_id, mascota_id, tipo_codigo, tipo, ciudad, estado,
            programado_para, termina_en, motivo_estado, requiere_autorizacion, autorizado)
        SELECT f.id, m.id, t.codigo, t.modalidad, f.ciudad, est.estado, prog,
            prog + make_interval(mins => t.duracion_min),
            CASE WHEN est.estado = 'cancelado' THEN 'La familia cancelo' END, false, false
        FROM familias f
        JOIN LATERAL (SELECT id FROM mascotas WHERE familia_id = f.id LIMIT 1) m ON true
        CROSS JOIN LATERAL generate_series(1, 6) AS k
        CROSS JOIN LATERAL (SELECT codigo, modalidad, duracion_min FROM tipos_servicio
                            WHERE activo ORDER BY codigo OFFSET k % 4 LIMIT 1) t
        CROSS JOIN LATERAL (SELECT CASE WHEN k <= 4 THEN 'completado'::estado_servicio
                                        WHEN k = 5 THEN 'agendado' ELSE 'cancelado' END
                                   AS estado) est
        CROSS JOIN LATERAL (SELECT date_trunc('day', now()) + interval '9 hours'
                                   + make_interval(days => CASE WHEN k = 5 THEN 3 ELSE -60 * k END)
                                   AS prog) p
        WHERE f.documento LIKE 'VOL%'
        """,
    ),
    (
        "mensajes",
        """
        INSERT INTO mensajes (familia_id, canal, direccion, destino, contenido, estado,
            variables, intentos, masivo, enviado_en)
        SELECT f.id, 'whatsapp', 'saliente', f.telefono, 'Recordatorio ' || k,
            CASE WHEN k % 3 = 0 THEN 'leido'::estado_mensaje ELSE 'entregado' END,
            '[]', 1, k % 5 = 0, now() - (k || ' days')::interval
        FROM familias f CROSS JOIN LATERAL generate_series(1, 40) AS k
        WHERE f.documento LIKE 'VOL%'
        """,
    ),
    (
        "usuarios de carga",
        """
        INSERT INTO usuarios (email, nombre, hashed_password, rol, activo)
        SELECT 'carga-' || perfil || '-' || lpad(k::text, 2, '0') || '@volumen.example.com',
            'Carga ' || perfil || ' ' || k, :clave,
            CASE perfil WHEN 'equipo' THEN 'comercial'::rol ELSE 'familia' END, true
        FROM unnest(ARRAY['equipo', 'portal']) AS perfil
        CROSS JOIN generate_series(1, :usuarios) AS k
        """,
    ),
    (
        "familias con portal",
        """
        UPDATE familias f SET usuario_portal_id = u.id
        FROM usuarios u
        WHERE u.email = 'carga-portal-' || lpad(substr(f.documento, 4)::int::text, 2, '0')
                        || '@volumen.example.com'
          AND f.documento LIKE 'VOL%' AND substr(f.documento, 4)::int <= :usuarios
        """,
    ),
    (
        "tareas",
        """
        INSERT INTO tareas (titulo, area, prioridad, estado, familia_id, vence_el, cerrada_en)
        SELECT 'Seguimiento ' || k, CASE WHEN k = 1 THEN 'comercial'::area_tarea
                                         ELSE 'operaciones' END,
            CASE k WHEN 1 THEN 'alta'::prioridad ELSE 'media' END,
            CASE WHEN k = 1 THEN 'abierta'::estado_tarea ELSE 'cerrada' END,
            f.id, current_date + k, CASE WHEN k = 1 THEN NULL ELSE now() END
        FROM familias f CROSS JOIN LATERAL generate_series(1, 2) AS k
        WHERE f.documento LIKE 'VOL%'
        """,
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--escala", type=float, default=1.0)
    escala = parser.parse_args().escala
    if settings.es_desplegado:
        raise SystemExit("datos_volumen solo corre en local, pruebas o CI")
    n = max(USUARIOS_CARGA, int(FAMILIAS * escala))
    parametros = {"n": n, "usuarios": USUARIOS_CARGA, "clave": hash_password(CLAVE_CARGA)}
    motor = create_engine(settings.DATABASE_URL_PROPIETARIO.replace("+asyncpg", "+psycopg"))
    with motor.begin() as conexion:
        existe = text("SELECT count(*) FROM familias WHERE documento LIKE :marca")
        if conexion.scalar(existe, {"marca": f"{_MARCA}%"}):
            print("El volumen ya existe; no se genera de nuevo")
            return
        conexion.execute(text("SELECT setseed(0.42)"))
        for tabla, sql in _PASOS:
            inicio = time.monotonic()
            filas = conexion.execute(text(sql), parametros).rowcount
            print(f"{tabla}: {filas} filas en {time.monotonic() - inicio:.1f} s")
        conexion.execute(text("ANALYZE"))
    total = motor.connect().scalar(text("SELECT count(*) FROM auditoria"))
    print(f"Listo: {n} familias; la bitacora tiene {total} registros")


if __name__ == "__main__":
    main()
