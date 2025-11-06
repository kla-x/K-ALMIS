"""add fields mainanance and disposal

Revision ID: 084eb931f64e
Revises: 1eb44413307a
Create Date: 2025-09-12 19:20:14.453033
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '084eb931f64e'
down_revision: Union[str, Sequence[str], None] = '1eb44413307a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Explicit enum type
disposal_status_enum = sa.Enum(
    'INITIATED',
    'SCHEDULED',
    'APPROVED',
    'EXECUTED',
    'CANCELLED',
    'UNDONE',
    name='disposalstatus'
)

maintenance_status_enum = sa.Enum(
    'INITIATED',
    'SCHEDULED',
    'APPROVED',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED',
    name='maintenancestatus'
)

def upgrade() -> None:
    """Upgrade schema."""
    # create enums first
    disposal_status_enum.create(op.get_bind(), checkfirst=True)
    maintenance_status_enum.create(op.get_bind(), checkfirst=True)

    # asset_disposals.status
    op.add_column(
        'asset_disposals',
        sa.Column('status', disposal_status_enum, nullable=True)
    )
    op.create_index(
        op.f('ix_asset_disposals_status'),
        'asset_disposals',
        ['status'],
        unique=False
    )

    # assets.department_id -> nullable
    op.alter_column(
        'assets',
        'department_id',
        existing_type=sa.VARCHAR(length=60),
        nullable=True
    )

    # maintenance_requests.maintenance_date
    op.add_column(
        'maintenance_requests',
        sa.Column('maintenance_date', sa.DateTime(), nullable=True)
    )

    # maintenance_requests.status type change
    op.alter_column(
        "maintenance_requests",
        "status",
        type_=sa.Enum("PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED", name="maintenancestatus"),
        postgresql_using="status::maintenancestatus"
    )

    op.create_index(
        op.f('ix_maintenance_requests_status'),
        'maintenance_requests',
        ['status'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_maintenance_requests_status'), table_name='maintenance_requests')
    op.alter_column(
        'maintenance_requests',
        'status',
        existing_type=maintenance_status_enum,
        type_=sa.VARCHAR(length=20),
        existing_nullable=True
    )
    op.drop_column('maintenance_requests', 'maintenance_date')

    op.alter_column(
        'assets',
        'department_id',
        existing_type=sa.VARCHAR(length=60),
        nullable=False
    )

    op.drop_index(op.f('ix_asset_disposals_status'), table_name='asset_disposals')
    op.drop_column('asset_disposals', 'status')

    # drop enums last
    disposal_status_enum.drop(op.get_bind(), checkfirst=True)
    maintenance_status_enum.drop(op.get_bind(), checkfirst=True)
