"""Create tables.

Revision ID: ea4c5954c633
Revises:
Create Date: 2023-09-22 14:36:00.228029

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ea4c5954c633"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "station_information",
        sa.Column("station_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=30), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("station_id"),
    )
    op.create_table(
        "station_status",
        sa.Column("station_id", sa.BigInteger(), nullable=False),
        sa.Column("datetime", sa.DateTime(), nullable=False),
        sa.Column("num_bikes_available", sa.Integer(), nullable=False),
        sa.Column(
            "num_bikes_available_types_mechanical",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "num_bikes_available_types_ebike", sa.Integer(), nullable=False
        ),
        sa.Column("num_docks_available", sa.Integer(), nullable=False),
        sa.Column("is_installed", sa.Boolean(), nullable=False),
        sa.Column("is_returning", sa.Boolean(), nullable=False),
        sa.Column("is_renting", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["station_information.station_id"],
        ),
        sa.PrimaryKeyConstraint("station_id", "datetime"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("station_status")
    op.drop_table("station_information")
    # ### end Alembic commands ###
