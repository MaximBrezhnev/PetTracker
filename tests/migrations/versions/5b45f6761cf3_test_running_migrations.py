"""test running migrations

Revision ID: 5b45f6761cf3
Revises:
Create Date: 2024-06-19 12:04:44.864215

"""
from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5b45f6761cf3"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "task_record",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("task_id"),
    )
    op.create_table(
        "user",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE ('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE ('utc', now())"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "pet",
        sa.Column("pet_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=30), nullable=False),
        sa.Column("species", sa.String(length=30), nullable=False),
        sa.Column("breed", sa.String(length=30), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE ('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE ('utc', now())"),
            nullable=False,
        ),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["user.user_id"],
        ),
        sa.PrimaryKeyConstraint("pet_id"),
    )
    op.create_table(
        "event",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.String(length=300), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE ('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("TIMEZONE ('utc', now())"),
            nullable=False,
        ),
        sa.Column("pet_id", sa.Uuid(), nullable=False),
        sa.Column("is_happened", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["pet_id"],
            ["pet.pet_id"],
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("event")
    op.drop_table("pet")
    op.drop_table("user")
    op.drop_table("task_record")
    # ### end Alembic commands ###
