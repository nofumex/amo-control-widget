"""security hardening schema updates"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260628_0002"
down_revision = "20260628_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("integration_client_id", sa.String(length=255), nullable=False, server_default=""))
    op.create_index("ix_tenants_integration_client_id", "tenants", ["integration_client_id"])
    op.create_index("ix_tenants_status_created", "tenants", ["status", "created_at"])
    op.create_unique_constraint("uq_tenant_account_integration", "tenants", ["account_id", "integration_client_id"])
    op.create_unique_constraint("uq_oauth_token_tenant", "oauth_tokens", ["tenant_id"])
    op.add_column("delivery_logs", sa.Column("idempotency_key", sa.String(length=255), nullable=False, server_default=""))
    op.create_index("ix_delivery_logs_idempotency_key", "delivery_logs", ["idempotency_key"])
    op.create_index("ix_delivery_tenant_status_created", "delivery_logs", ["tenant_id", "status", "created_at"])
    op.add_column("event_inbox", sa.Column("dedup_key", sa.String(length=128), nullable=True))
    op.create_unique_constraint("uq_event_inbox_source_dedup", "event_inbox", ["source", "dedup_key"])
    op.create_index("ix_event_inbox_tenant_status_received", "event_inbox", ["tenant_id", "status", "received_at"])
    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state_hash", sa.String(length=128), nullable=False),
        sa.Column("account_id_hint", sa.BigInteger(), nullable=True),
        sa.Column("subdomain_hint", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("referer", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("state_hash", name="uq_oauth_state_hash"),
    )
    op.create_index("ix_oauth_states_status_expires", "oauth_states", ["status", "expires_at"])
    op.create_table(
        "security_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ok"),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_security_audit_logs_tenant_id", "security_audit_logs", ["tenant_id"])
    op.create_index("ix_security_audit_logs_event_type", "security_audit_logs", ["event_type"])
    op.create_index(
        "ix_security_audit_tenant_event_created",
        "security_audit_logs",
        ["tenant_id", "event_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("security_audit_logs")
    op.drop_table("oauth_states")
    op.drop_index("ix_event_inbox_tenant_status_received", table_name="event_inbox")
    op.drop_constraint("uq_event_inbox_source_dedup", "event_inbox", type_="unique")
    op.drop_column("event_inbox", "dedup_key")
    op.drop_index("ix_delivery_tenant_status_created", table_name="delivery_logs")
    op.drop_index("ix_delivery_logs_idempotency_key", table_name="delivery_logs")
    op.drop_column("delivery_logs", "idempotency_key")
    op.drop_constraint("uq_oauth_token_tenant", "oauth_tokens", type_="unique")
    op.drop_constraint("uq_tenant_account_integration", "tenants", type_="unique")
    op.drop_index("ix_tenants_status_created", table_name="tenants")
    op.drop_index("ix_tenants_integration_client_id", table_name="tenants")
    op.drop_column("tenants", "integration_client_id")
