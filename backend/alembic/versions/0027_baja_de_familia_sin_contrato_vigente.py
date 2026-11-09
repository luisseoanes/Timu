"""baja de familia sin contrato vigente

Al desenredar los dominios (docs/deuda-ciclos-dominios.md), la baja de una familia pasa a
orquestarse en afiliaciones.ciclo: cancela el contrato vigente y despues marca la ficha con
familias.dar_de_baja. Esa funcion ya no cancela el contrato por su cuenta, asi que la regla
pasa a la base: una familia dada de baja no tiene contrato vigente, lo haga quien lo haga.
Sin esto una familia que ya se fue seguiria con cuotas, avisos de mora y cobro a la tarjeta.

Se vigila por los dos lados: no se marca la baja de una familia con contrato vigente, y no se
crea ni se reactiva un contrato vigente para una familia dada de baja (Python ya lo rechazaba
en cartera.crear_contrato; el estado del contrato no tiene grafo de transiciones, asi que un
UPDATE podia reactivar uno cancelado).

SECURITY DEFINER para ver la otra tabla sea cual sea el perfil que escribe. Los estados
vigentes son los de VIGENTES en cartera.contratos (activa, en_mora, congelada), los mismos
que usa anonimizar_familia() de la 0022.

Revision ID: 0027
Revises: 0026
Create Date: 2026-11-10 12:00:00
"""

from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

_VIGENTES = "('activa', 'en_mora', 'congelada')"


def upgrade() -> None:
    op.execute(
        f"""
        CREATE FUNCTION familia_sin_contrato_vigente() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM contratos
                WHERE familia_id = NEW.id AND estado IN {_VIGENTES}
            ) THEN
                RAISE EXCEPTION
                    'La familia % tiene un contrato vigente: cancelelo antes de la baja', NEW.id
                    USING ERRCODE = 'check_violation',
                          CONSTRAINT = 'familias_baja_sin_contrato_vigente';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER tr_familias_baja_sin_contrato_vigente"
        " BEFORE UPDATE OF dada_de_baja_en ON familias FOR EACH ROW"
        " WHEN (OLD.dada_de_baja_en IS NULL AND NEW.dada_de_baja_en IS NOT NULL)"
        " EXECUTE FUNCTION familia_sin_contrato_vigente()"
    )
    op.execute(
        """
        CREATE FUNCTION contrato_vigente_de_familia_activa() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM familias
                WHERE id = NEW.familia_id AND dada_de_baja_en IS NOT NULL
            ) THEN
                RAISE EXCEPTION
                    'La familia % esta dada de baja: no admite un contrato vigente',
                    NEW.familia_id
                    USING ERRCODE = 'check_violation',
                          CONSTRAINT = 'contratos_vigente_de_familia_activa';
            END IF;
            RETURN NEW;
        END
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER tr_contratos_vigente_de_familia_activa"
        " BEFORE INSERT OR UPDATE OF estado, familia_id ON contratos FOR EACH ROW"
        f" WHEN (NEW.estado IN {_VIGENTES})"
        " EXECUTE FUNCTION contrato_vigente_de_familia_activa()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER tr_contratos_vigente_de_familia_activa ON contratos")
    op.execute("DROP FUNCTION contrato_vigente_de_familia_activa()")
    op.execute("DROP TRIGGER tr_familias_baja_sin_contrato_vigente ON familias")
    op.execute("DROP FUNCTION familia_sin_contrato_vigente()")
