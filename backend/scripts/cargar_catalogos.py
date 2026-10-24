"""F0-09 Carga repetible de catalogos maestros y de las reglas iniciales (F0-12).

Uso: docker compose exec api python -m scripts.cargar_catalogos
"""

from app.core.database import sesion_worker
from app.models import Base  # noqa: F401  registra todos los modelos
from app.modules.catalogos.service import cargar
from app.modules.reglas.service import sembrar


def main() -> None:
    # Los servicios son sincronos: se usa la misma sesion que los workers, que confirma
    # al salir bien y revierte ante cualquier error.
    with sesion_worker() as db:
        resultado = cargar(db)
        reglas = sembrar(db)
    for tabla, conteo in resultado.items():
        print(f"{tabla}: {conteo['creados']} creados, {conteo['actualizados']} actualizados")
    print(f"reglas: {reglas} creadas (las existentes no se modifican)")


if __name__ == "__main__":
    main()
