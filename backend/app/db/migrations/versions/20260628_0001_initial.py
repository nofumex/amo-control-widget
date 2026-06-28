"""initial multi-tenant schema"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260628_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.BigInteger(), nullable=True),
        sa.Column("subdomain", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("base_url", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("mode", sa.String(length=32), nullable=False, server_default="private"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tenants_account_id", "tenants", ["account_id"])
    op.create_index("ix_tenants_subdomain", "tenants", ["subdomain"])
    jsonb = postgresql.JSONB(astext_type=sa.Text())
    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_oauth_tokens_tenant_id", "oauth_tokens", ["tenant_id"])
    op.create_table(
        "report_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("timezone", sa.String(length=128), nullable=False, server_default="UTC"),
        sa.Column("work_session_gap_minutes", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("incoming_call_min_duration_seconds", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("outgoing_call_min_duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled_activity_events", jsonb, nullable=False, server_default="{}"),
        sa.Column("enabled_counter_events", jsonb, nullable=False, server_default="{}"),
        sa.Column("enabled_penalty_events", jsonb, nullable=False, server_default="{}"),
        sa.Column("stage_transition_filters", jsonb, nullable=False, server_default="{}"),
        sa.Column("selected_user_ids", jsonb, nullable=False, server_default="[]"),
        sa.Column("user_groups", jsonb, nullable=False, server_default="{}"),
        sa.Column("excluded_user_ids", jsonb, nullable=False, server_default="[]"),
        sa.Column("build_hour", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("send_hour", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("auto_send_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("live_sync_interval_seconds", sa.Integer(), nullable=False, server_default="900"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "telegram_channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("bot_token_encrypted", sa.Text(), nullable=False, server_default=""),
        sa.Column("admin_chat_id_encrypted", sa.Text(), nullable=False, server_default=""),
        sa.Column("admin_username", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("last_test_status", sa.Text(), nullable=False, server_default=""),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "report_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(length=128), nullable=False),
        sa.Column("config_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("config_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("raw_json", jsonb, nullable=False, server_default="{}"),
        sa.Column("rendered_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="built"),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_window_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "report_date", name="uq_report_snapshot_tenant_date"),
    )
    op.create_table(
        "delivery_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), sa.ForeignKey("report_snapshots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="telegram"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "call_note_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("note_id", sa.BigInteger(), nullable=False),
        sa.Column("payload_json", jsonb, nullable=False, server_default="{}"),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "entity_type", "entity_id", "note_id", name="uq_call_note"),
    )
    op.create_table(
        "sync_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("last_events_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_tasks_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "event_inbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("payload_json", jsonb, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    for table in (
        "event_inbox",
        "sync_state",
        "call_note_cache",
        "delivery_logs",
        "report_snapshots",
        "telegram_channels",
        "report_configs",
        "oauth_tokens",
        "tenants",
    ):
        op.drop_table(table)

