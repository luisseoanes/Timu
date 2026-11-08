"""rol de la aplicacion: timu_app, sin superusuario ni BYPASSRLS

La aplicacion deja de conectarse con el dueno del esquema. timu_app solo tiene permisos
sobre los datos (nunca DDL) y la base le aplica sus restricciones, triggers y politicas.
Los permisos por defecto hacen que las tablas que creen migraciones posteriores le
lleguen solas. El LOGIN y la clave se los da `inicializar` (o quien administre el
ambiente): una clave no se escribe en una migracion.

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-04 18:00:00
"""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'timu_app') THEN
                CREATE ROLE timu_app NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
            END IF;
        END
        $$
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO timu_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO timu_app")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO timu_app")
    # El historial de migraciones es del dueno del esquema.
    op.execute("REVOKE ALL ON alembic_version FROM timu_app")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO timu_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO timu_app"
    )


def downgrade() -> None:
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE USAGE, SELECT ON SEQUENCES FROM timu_app"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM timu_app"
    )
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM timu_app")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM timu_app")
    op.execute("REVOKE USAGE ON SCHEMA public FROM timu_app")
    # El rol es del cluster, no de la base: se deja si otra base lo sigue usando.
