"""added enum

Revision ID: bc5cea221cf2
Revises: 5b45f6761cf3
Create Date: 2024-06-19 12:12:39.475789

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "bc5cea221cf2"
down_revision: Union[str, None] = "5b45f6761cf3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "pet",
        sa.Column(
            "gender", sa.Enum("male", "female", name="petgenderenum"), nullable=False
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("pet", "gender")
    # ### end Alembic commands ###
