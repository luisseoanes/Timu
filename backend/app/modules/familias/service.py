from uuid import UUID

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session

from app.core.auditoria import Accion, RegistroAuditoria
from app.core.enums import EstadoAfiliacion
from app.core.errores import Conflicto, NoEncontrado, ReglaNegocio
from app.core.eventos import EventoDominio
from app.core.outbox import publicar
from app.core.scope import Alcance, permite, restringir
from app.core.tiempo import ahora, hoy
from app.integrations import geocodificacion
from app.modules.archivos import service as archivos
from app.modules.archivos.models import Archivo
from app.modules.catalogos import service as catalogos
from app.modules.catalogos.models import Ciudad
from app.modules.familias.models import Familia, Mascota
from app.modules.familias.schemas import (
    FamiliaCreate,
    FamiliaUpdate,
    FormularioFamilia,
    MascotaCreate,
    MascotaRead,
    MascotaUpdate,
    ResultadoFormulario,
)

EVENTO_UBICACION = "familia.ubicacion_cambiada"

ORDEN = {
    "created_at": Familia.created_at,
    "titular_nombre": Familia.titular_nombre,
    "ciudad": Familia.ciudad,
    "estado": Familia.estado,
}


def consulta_listado(
    alcance: Alcance,
    *,
    q: str | None = None,
    ciudad: str | None = None,
    estado: EstadoAfiliacion | None = None,
    incluir_bajas: bool = False,
) -> Select[tuple[Familia]]:
    """6.16 Segmentacion: filtros combinables para campanas y reportes.

    El alcance se aplica antes que cualquier filtro: para el portal, una familia solo
    se ve a si misma por mucho que juegue con los parametros de busqueda.
    """
    stmt = restringir(select(Familia), Familia, alcance)
    if not incluir_bajas:
        stmt = stmt.where(Familia.dada_de_baja_en.is_(None))
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(
            or_(
                Familia.titular_nombre.ilike(patron),
                Familia.documento.ilike(patron),
                Familia.telefono.ilike(patron),
            )
        )
    if ciudad:
        stmt = stmt.where(Familia.ciudad == ciudad)
    if estado:
        stmt = stmt.where(Familia.estado == estado)
    return stmt


def obtener(db: Session, familia_id: UUID, alcance: Alcance | None = None) -> Familia:
    """Lectura por id. Con alcance de portal, pedir otra familia da el mismo 404 que una
    inexistente: no se distingue "no existe" de "no es tuya"."""
    familia = db.get(Familia, familia_id)
    if familia is None or (alcance is not None and not permite(familia, alcance)):
        raise NoEncontrado("Familia no encontrada")
    return familia


def _verificar_documento(
    db: Session, tipo: str, documento: str, excluir: UUID | None = None
) -> None:
    stmt = select(Familia.id).where(Familia.tipo_documento == tipo, Familia.documento == documento)
    if excluir:
        stmt = stmt.where(Familia.id != excluir)
    if db.scalar(stmt):
        raise Conflicto(f"Ya existe una familia con el documento {tipo} {documento}")


def _mascotas_validas(db: Session, mascotas: list[MascotaCreate]) -> list[Mascota]:
    resultado = []
    for m in mascotas:
        datos = m.model_dump()
        datos["especie"] = catalogos.especie_valida(db, m.especie)
        resultado.append(Mascota(**datos))
    return resultado


def _programar_geocodificacion(db: Session, familia: Familia) -> None:
    publicar(db, EventoDominio(EVENTO_UBICACION, {"familia_id": str(familia.id)}))


def crear(db: Session, data: FamiliaCreate, *, origen: str = "panel") -> Familia:
    _verificar_documento(db, data.tipo_documento, data.documento)
    datos = data.model_dump(exclude={"mascotas"})
    datos["ciudad"] = catalogos.ciudad_valida(db, data.ciudad)
    familia = Familia(**datos, origen=origen)
    familia.mascotas = _mascotas_validas(db, data.mascotas)
    if data.latitud is not None and data.longitud is not None:
        familia.geo_precision = "manual"
    db.add(familia)
    db.flush()
    if familia.direccion and familia.geo_precision != "manual":
        _programar_geocodificacion(db, familia)
    return familia


def actualizar(db: Session, familia: Familia, data: FamiliaUpdate) -> Familia:
    cambios = data.model_dump(exclude_unset=True)
    if "ciudad" in cambios and cambios["ciudad"]:
        cambios["ciudad"] = catalogos.ciudad_valida(db, cambios["ciudad"])
    manual = cambios.get("latitud") is not None and cambios.get("longitud") is not None
    ubicacion_cambio = any(
        k in cambios and cambios[k] != getattr(familia, k) for k in ("direccion", "ciudad")
    )
    for campo, valor in cambios.items():
        setattr(familia, campo, valor)
    if manual:
        familia.geo_precision = "manual"
    elif ubicacion_cambio:
        # La ubicacion anterior ya no corresponde: se recalcula.
        familia.latitud = familia.longitud = familia.geo_precision = None
        if familia.direccion:
            _programar_geocodificacion(db, familia)
    db.flush()
    return familia


def cambiar_estado(
    db: Session, familia: Familia, estado: EstadoAfiliacion, motivo: str | None = None
) -> Familia:
    """6.23 Unico punto para cambiar el estado de afiliacion; la auditoria guarda el cambio
    y cartera y servicios se enganchan aqui para propagar sus efectos."""
    if familia.dada_de_baja_en is not None:
        raise ReglaNegocio("La familia esta dada de baja")
    if familia.estado == estado:
        return familia
    familia.estado = estado
    if motivo:
        familia.notas = f"{familia.notas or ''}\n[{ahora():%Y-%m-%d}] {estado}: {motivo}".strip()
    db.flush()
    return familia


def dar_de_baja(db: Session, familia: Familia, motivo: str) -> Familia:
    """F1-FAM-01 Baja logica: la familia deja de aparecer, pero su historia se conserva."""
    if familia.dada_de_baja_en is not None:
        raise ReglaNegocio("La familia ya esta dada de baja")
    from app.modules.cartera import service as cartera
    from app.modules.planes import service as planes

    # Sin esto el contrato seguiria vigente: cuotas, avisos de mora y cobro a la tarjeta
    # de una familia que ya se fue.
    contrato = planes.contrato_vigente(db, familia.id)
    if contrato is not None:
        cartera.cancelar(db, contrato, f"Baja de la familia: {motivo}")
    familia.estado = EstadoAfiliacion.CANCELADA
    familia.dada_de_baja_en = ahora()
    familia.motivo_baja = motivo
    db.flush()
    return familia


def historial(db: Session, familia_id: UUID, solo_estado: bool) -> list[RegistroAuditoria]:
    """F1-FAM-01 Historial de cambios tomado de la bitacora de auditoria."""
    stmt = select(RegistroAuditoria).where(
        RegistroAuditoria.entidad == "familias",
        RegistroAuditoria.entidad_id == str(familia_id),
    )
    if solo_estado:
        stmt = stmt.where(RegistroAuditoria.accion == Accion.CAMBIO_ESTADO)
    return list(db.scalars(stmt.order_by(RegistroAuditoria.created_at)))


def habilitar_portal(db: Session, familia: Familia) -> Familia:
    """F1-AUT-04 Acceso propio de la familia al portal; recibe el enlace de activacion."""
    from app.modules.auth.service import crear_usuario_portal

    if familia.usuario_portal_id is None:
        usuario = crear_usuario_portal(
            db, nombre=familia.titular_nombre, email=familia.email, telefono=familia.telefono
        )
        vinculada = db.scalar(select(Familia.id).where(Familia.usuario_portal_id == usuario.id))
        if vinculada:
            raise Conflicto("Ese acceso de portal ya pertenece a otra familia")
        familia.usuario_portal_id = usuario.id
        db.flush()
    return familia


def familia_de_usuario(db: Session, usuario_id: UUID) -> Familia:
    familia = db.scalar(
        select(Familia).where(
            Familia.usuario_portal_id == usuario_id, Familia.dada_de_baja_en.is_(None)
        )
    )
    if familia is None:
        raise NoEncontrado("La cuenta no esta vinculada a una familia activa")
    return familia


# --- Mascotas (F1-FAM-02) -------------------------------------------------------------------


def obtener_mascota(db: Session, mascota_id: UUID) -> Mascota:
    mascota = db.get(Mascota, mascota_id)
    if mascota is None:
        raise NoEncontrado("Mascota no encontrada")
    return mascota


def agregar_mascota(db: Session, familia: Familia, data: MascotaCreate) -> Mascota:
    if familia.dada_de_baja_en is not None:
        raise ReglaNegocio("No se pueden agregar mascotas a una familia dada de baja")
    (mascota,) = _mascotas_validas(db, [data])
    afiliada = _validar_contra_plan(db, familia, mascota)
    familia.mascotas.append(mascota)
    db.flush()
    if afiliada:
        from app.modules.preventivos import service as preventivos

        # F1-AFI-03 La mascota que entra a un plan vigente recibe su calendario preventivo.
        preventivos.calendario_inicial(db, mascota, hoy())
    return mascota


def _validar_contra_plan(db: Session, familia: Familia, mascota: Mascota) -> bool:
    """F1-PLA-03 Con contrato vigente, la mascota nueva debe caber en el plan (o pagar el
    adicional que defina la regla) y ser de una especie que el plan cubre."""
    from app.modules.planes import service as planes

    contrato = planes.contrato_vigente(db, familia.id)
    if contrato is None:
        return False
    plan = planes.obtener(db, contrato.plan_id)
    if plan.especies and mascota.especie not in plan.especies:
        raise ReglaNegocio(f"El plan {plan.nombre} no cubre la especie {mascota.especie}")
    planes.ajustar_por_mascotas(db, familia, "mascota_alta")
    return True


def actualizar_mascota(db: Session, mascota: Mascota, data: MascotaUpdate) -> Mascota:
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(mascota, campo, valor)
    db.flush()
    return mascota


def dar_de_baja_mascota(db: Session, mascota: Mascota, motivo: str) -> Mascota:
    if not mascota.activa:
        raise ReglaNegocio("La mascota ya esta dada de baja")
    mascota.activa = False
    mascota.dada_de_baja_en = ahora()
    mascota.motivo_baja = motivo
    db.flush()
    from app.modules.planes import service as planes

    familia = obtener(db, mascota.familia_id)
    planes.ajustar_por_mascotas(db, familia, "mascota_baja")
    return mascota


def subir_foto(
    db: Session, mascota: Mascota, contenido: bytes, nombre: str | None, usuario_id: UUID | None
) -> Mascota:
    archivo = archivos.subir(
        db, contenido, nombre=nombre, proposito="foto_mascota", usuario_id=usuario_id
    )
    mascota.foto_archivo_id = archivo.id
    db.flush()
    return mascota


def mascota_read(db: Session, mascota: Mascota) -> MascotaRead:
    lectura = MascotaRead.model_validate(mascota)
    if mascota.foto_archivo_id:
        archivo = db.get(Archivo, mascota.foto_archivo_id)
        lectura.foto_url = archivos.url(archivo) if archivo else None
    return lectura


# --- Geocodificacion (F1-FAM-05) --------------------------------------------------------------


def geocodificar(db: Session, familia_id: UUID) -> str | None:
    """Ubica la direccion; si el proveedor no la encuentra, usa el centro de la ciudad
    marcado como aproximado para que operaciones sepa que debe confirmarla."""
    familia = db.get(Familia, familia_id)
    if familia is None or not familia.direccion or familia.geo_precision == "manual":
        return None
    coordenadas = geocodificacion.geocodificar(familia.direccion, familia.ciudad)
    if coordenadas:
        familia.latitud, familia.longitud = coordenadas
        familia.geo_precision = "direccion"
    else:
        ciudad = db.scalar(select(Ciudad).where(Ciudad.nombre == familia.ciudad))
        if ciudad is None or ciudad.latitud is None:
            return None
        familia.latitud, familia.longitud = ciudad.latitud, ciudad.longitud
        familia.geo_precision = "ciudad"
    db.flush()
    return familia.geo_precision


# --- Autollenado desde formularios (F1-FAM-03) ------------------------------------------------

_CAMPOS_COMPLETABLES = ("email", "direccion", "titular_nombre")


def desde_formulario(db: Session, data: FormularioFamilia) -> ResultadoFormulario:
    """Crea la familia o completa la existente con el mismo documento.

    Como el formulario es publico, sobre una familia existente solo se llenan campos vacios
    y se agregan mascotas nuevas: nunca se sobrescribe lo que el equipo ya valido.
    """
    familia = db.scalar(
        select(Familia).where(
            and_(Familia.tipo_documento == data.tipo_documento, Familia.documento == data.documento)
        )
    )
    if familia is None:
        nueva = FamiliaCreate(
            titular_nombre=data.titular_nombre,
            tipo_documento=data.tipo_documento,
            documento=data.documento,
            email=data.email,
            telefono=data.telefono,
            ciudad=data.ciudad,
            direccion=data.direccion,
            mascotas=data.mascotas,
        )
        familia = crear(db, nueva, origen=data.origen)
        return ResultadoFormulario(
            familia_id=familia.id,
            creada=True,
            campos_completados=[],
            mascotas_agregadas=[m.nombre for m in familia.mascotas],
        )

    completados = []
    for campo in _CAMPOS_COMPLETABLES:
        valor = getattr(data, campo)
        if valor and not getattr(familia, campo):
            setattr(familia, campo, str(valor))
            completados.append(campo)
    if "direccion" in completados:
        _programar_geocodificacion(db, familia)

    existentes = {m.nombre.strip().lower() for m in familia.mascotas}
    agregadas = []
    for m in data.mascotas:
        if m.nombre.strip().lower() not in existentes:
            agregar_mascota(db, familia, m)
            agregadas.append(m.nombre)
    db.flush()
    return ResultadoFormulario(
        familia_id=familia.id,
        creada=False,
        campos_completados=completados,
        mascotas_agregadas=agregadas,
    )
