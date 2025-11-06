"""add cost fields and sup to sys

Revision ID: f77bd06c4d70
Revises: a0ce087e3924
Create Date: 2025-10-01 22:28:13.833942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f77bd06c4d70'
down_revision: Union[str, Sequence[str], None] = 'a0ce087e3924'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create the ENUM type first
    maintenanceoutcome_enum = sa.Enum('FIXED', 'NOT_FIXED', name='maintenanceoutcome')
    maintenanceoutcome_enum.create(op.get_bind(), checkfirst=True)
    
    # Now add the columns
    op.add_column('maintenance_requests', sa.Column('cost', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('maintenance_requests', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('maintenance_requests', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.add_column('maintenance_requests', sa.Column('duration', sa.Interval(), nullable=True))
    op.add_column('maintenance_requests', sa.Column('outcome', sa.Enum('FIXED', 'NOT_FIXED', name='maintenanceoutcome'), nullable=True))


def downgrade():
    # Drop the columns first
    op.drop_column('maintenance_requests', 'outcome')
    op.drop_column('maintenance_requests', 'duration')
    op.drop_column('maintenance_requests', 'completed_at')
    op.drop_column('maintenance_requests', 'started_at')
    op.drop_column('maintenance_requests', 'cost')
    
    # Then drop the ENUM type
    sa.Enum(name='maintenanceoutcome').drop(op.get_bind(), checkfirst=True)