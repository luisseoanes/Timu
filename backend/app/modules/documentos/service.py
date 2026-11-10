"""6.1 Documentos de la familia y de sus mascotas.

Reune en una sola vista lo que el equipo sube a la ficha (`documentos_familia`) y lo que la
plataforma genera para la familia: el PDF de cada contrato, los carnets emitidos y los
adjuntos y formulas de la historia clinica. Por eso vive en su propio dominio: lee de
cartera, preventivos y clinica, y ninguno de ellos depende de el.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import CategoriaDocumento
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ahora
from app.modules.archivos import service as archivos
from app.modules.archivos.models import Archivo
from app.modules.cartera.models import Contrato
from app.modules.clinica.models import AdjuntoClinico, Formula, HistoriaClinica
from app.modules.documentos.models import DocumentoFamilia
from app.modules.familias.models import Familia, Mascota
from app.modules.preventivos.models import CarnetEmitido

Origen = Literal["subido", "contrato", "carnet", "adjunto_clinico", "formula"]


class DocumentoIn(BaseModel):
    categoria: CategoriaDocumento
    descripcion: str | None = Field(default=None, max_length=255)
    mascota_id: UUID | None = None
    visible_familia: bool = False


class DocumentoUpdate(BaseModel):
    categoria: CategoriaDocumento | None = None
    descripcion: str | None = Field(default=None, max_length=255)
    visible_familia: bool | None = None


class DocumentoRead(BaseModel):
    """Una fila de la vista de documentos. `documento_id` solo lo tienen los subidos: son los
    unicos que se editan o se quitan; los generados se gestionan donde nacen."""

    model_config = ConfigDict(from_attributes=True)

    archivo_id: UUID
    documento_id: UUID | None = None
    origen: Origen
    categoria: CategoriaDocumento | None = None
    descripcion: str | None = None
    mascota_id: UUID | None = None
    nombre: str
    content_type: str
    tamano_bytes: int
    visible_familia: bool
    creado_en: datetime
    url: str | None = Field(default=None, description="Firmada y temporal; vacia si se purgo")


def _limpia(descripcion: str | None) -> str | None:
    return (descripcion or "").strip() or None


def _mascota_de(db: Session, familia: Familia, mascota_id: UUID | None) -> None:
    if mascota_id is None:
        return
    mascota = db.get(Mascota, mascota_id)
    if mascota is None or mascota.familia_id != familia.id:
        raise ReglaNegocio("La mascota no pertenece a la familia")


def subir(
    db: Session,
    familia: Familia,
    contenido: bytes,
    nombre: str | None,
    datos: DocumentoIn,
    usuario_id: UUID | None,
) -> DocumentoFamilia:
    """PDF o imagen de hasta 10 MB, validado por su contenido y no por su extension."""
    if familia.dada_de_baja_en is not None:
        raise ReglaNegocio("La familia esta dada de baja")
    _mascota_de(db, familia, datos.mascota_id)
    archivo = archivos.subir(
        db, contenido, nombre=nombre, proposito="documento_familia", usuario_id=usuario_id
    )
    documento = DocumentoFamilia(
        familia_id=familia.id,
        mascota_id=datos.mascota_id,
        archivo_id=archivo.id,
        categoria=datos.categoria,
        descripcion=_limpia(datos.descripcion),
        visible_familia=datos.visible_familia,
    )
    db.add(documento)
    db.flush()
    return documento


def obtener(db: Session, documento_id: UUID) -> DocumentoFamilia:
    documento = db.get(DocumentoFamilia, documento_id)
    if documento is None or not documento.activo:
        raise NoEncontrado("Documento no encontrado")
    return documento


def actualizar(db: Session, documento: DocumentoFamilia, data: DocumentoUpdate) -> DocumentoFamilia:
    cambios = data.model_dump(exclude_unset=True)
    vaciados = [c for c, v in cambios.items() if v is None and c != "descripcion"]
    if vaciados:
        raise ReglaNegocio(f"No se puede dejar vacio: {', '.join(vaciados)}")
    if "descripcion" in cambios:
        cambios["descripcion"] = _limpia(cambios["descripcion"])
    for campo, valor in cambios.items():
        setattr(documento, campo, valor)
    db.flush()
    return documento


def dar_de_baja(db: Session, documento: DocumentoFamilia) -> None:
    documento.activo = False
    documento.dado_de_baja_en = ahora()
    db.flush()


def leer(db: Session, documento: DocumentoFamilia) -> DocumentoRead:
    archivo = db.get(Archivo, documento.archivo_id)
    assert archivo is not None  # la llave foranea lo garantiza
    return _fila(archivo, "subido", documento=documento)


def _fila(
    archivo: Archivo,
    origen: Origen,
    *,
    documento: DocumentoFamilia | None = None,
    descripcion: str | None = None,
    mascota_id: UUID | None = None,
    visible: bool = True,
) -> DocumentoRead:
    return DocumentoRead(
        archivo_id=archivo.id,
        documento_id=documento.id if documento else None,
        origen=origen,
        categoria=documento.categoria if documento else None,  # type: ignore[arg-type]
        descripcion=documento.descripcion if documento else descripcion,
        mascota_id=documento.mascota_id if documento else mascota_id,
        nombre=archivo.nombre_original,
        content_type=archivo.content_type,
        tamano_bytes=archivo.tamano_bytes,
        visible_familia=documento.visible_familia if documento else visible,
        creado_en=archivo.created_at,
        url=None if archivo.purgado_en else archivos.url(archivo),
    )


def listar(
    db: Session, familia: Familia, *, mascota_id: UUID | None = None, para_familia: bool = False
) -> list[DocumentoRead]:
    """Todos los documentos de la familia, del mas reciente al mas antiguo. Con `mascota_id`,
    solo los de esa mascota (los contratos son de la familia y no salen).

    Para la familia (portal): los subidos que el equipo marco visibles, sus contratos y sus
    carnets. Los adjuntos y las formulas los ve en la historia clinica, que solo muestra lo
    firmado."""
    filas: list[DocumentoRead] = []

    subidos = (
        select(DocumentoFamilia, Archivo)
        .join(Archivo, Archivo.id == DocumentoFamilia.archivo_id)
        .where(DocumentoFamilia.familia_id == familia.id, DocumentoFamilia.activo.is_(True))
    )
    if para_familia:
        subidos = subidos.where(DocumentoFamilia.visible_familia.is_(True))
    if mascota_id is not None:
        subidos = subidos.where(DocumentoFamilia.mascota_id == mascota_id)
    filas += [_fila(a, "subido", documento=d) for d, a in db.execute(subidos).tuples()]

    if mascota_id is None:
        contratos = (
            select(Contrato.numero, Archivo)
            .join(Archivo, Archivo.id == Contrato.documento_archivo_id)
            .where(Contrato.familia_id == familia.id)
        )
        filas += [
            _fila(a, "contrato", descripcion=f"Contrato {numero}")
            for numero, a in db.execute(contratos).tuples()
        ]

    carnets = (
        select(CarnetEmitido.codigo, Mascota.id, Mascota.nombre, Archivo)
        .join(Mascota, Mascota.id == CarnetEmitido.mascota_id)
        .join(Archivo, Archivo.id == CarnetEmitido.archivo_id)
        .where(Mascota.familia_id == familia.id)
    )
    if mascota_id is not None:
        carnets = carnets.where(Mascota.id == mascota_id)
    filas += [
        _fila(a, "carnet", descripcion=f"Carnet de {nombre} ({codigo})", mascota_id=mid)
        for codigo, mid, nombre, a in db.execute(carnets).tuples()
    ]

    if not para_familia:
        adjuntos = (
            select(
                AdjuntoClinico.descripcion,
                HistoriaClinica.mascota_id,
                HistoriaClinica.estado,
                Archivo,
            )
            .join(HistoriaClinica, HistoriaClinica.id == AdjuntoClinico.historia_id)
            .join(Archivo, Archivo.id == AdjuntoClinico.archivo_id)
            .where(HistoriaClinica.familia_id == familia.id)
        )
        formulas = (
            select(HistoriaClinica.mascota_id, HistoriaClinica.estado, Archivo)
            .select_from(Formula)
            .join(HistoriaClinica, HistoriaClinica.id == Formula.historia_id)
            .join(Archivo, Archivo.id == Formula.archivo_id)
            .where(HistoriaClinica.familia_id == familia.id)
        )
        if mascota_id is not None:
            adjuntos = adjuntos.where(HistoriaClinica.mascota_id == mascota_id)
            formulas = formulas.where(HistoriaClinica.mascota_id == mascota_id)
        # La familia los ve en su historia clinica una vez firmada, no en el borrador.
        filas += [
            _fila(a, "adjunto_clinico", descripcion=d, mascota_id=m, visible=e != "borrador")
            for d, m, e, a in db.execute(adjuntos).tuples()
        ]
        filas += [
            _fila(a, "formula", descripcion="Formula medica", mascota_id=m, visible=e != "borrador")
            for m, e, a in db.execute(formulas).tuples()
        ]

    return sorted(filas, key=lambda f: (f.creado_en, str(f.archivo_id)), reverse=True)
