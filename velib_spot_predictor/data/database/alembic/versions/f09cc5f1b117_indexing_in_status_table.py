"""Indexing in status table.

Revision ID: f09cc5f1b117
Revises: 4e5f3afbc9c6
Create Date: 2023-09-23 01:43:56.429909

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f09cc5f1b117"
down_revision: Union[str, None] = "4e5f3afbc9c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        op.f("ix_station_status_datetime"),
        "station_status",
        ["datetime"],
        unique=False,
    )
    op.create_index(
        op.f("ix_station_status_station_id"),
        "station_status",
        ["station_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_station_status_station_id"), table_name="station_status"
    )
    op.drop_index(
        op.f("ix_station_status_datetime"), table_name="station_status"
    )
    # ### end Alembic commands ###