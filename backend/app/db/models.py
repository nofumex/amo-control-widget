from __future__ import annotations

import datetime as dt
from typing import Any

from app.db.base import Base
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

JSONType = JSONB


class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("account_id", "integration_client_id", name="uq_tenant_account_integration"),
        Index("ix_tenants_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    subdomain: Mapped[str] = mapped_column(String(255), default="", index=True)
    base_url: Mapped[str] = mapped_column(String(512), default="")
    integration_client_id: Mapped[str] = mapped_column(String(255), default="", index=True)
    mode: Mapped[str] = mapped_column(String(32), default="private")
    status: Mapped[str] = mapped_column(String(32), default="active")

    tokens: Mapped[list[OAuthToken]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class OAuthToken(TimestampMixin, Base):
    __tablename__ = "oauth_tokens"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_oauth_token_tenant"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    access_token_encrypted: Mapped[str] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    scope: Mapped[str] = mapped_column(Text, default="")

    tenant: Mapped[Tenant] = relationship(back_populates="tokens")


class ReportConfig(TimestampMixin, Base):
    __tablename__ = "report_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(128), default="UTC")
    work_session_gap_minutes: Mapped[int] = mapped_column(Integer, default=10)
    incoming_call_min_duration_seconds: Mapped[int] = mapped_column(Integer, default=30)
    outgoing_call_min_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    enabled_activity_events: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    enabled_counter_events: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    enabled_penalty_events: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    stage_transition_filters: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    selected_user_ids: Mapped[list[int]] = mapped_column(JSONType, default=list)
    user_groups: Mapped[dict[str, str]] = mapped_column(JSONType, default=dict)
    excluded_user_ids: Mapped[list[int]] = mapped_column(JSONType, default=list)
    build_hour: Mapped[int] = mapped_column(Integer, default=1)
    send_hour: Mapped[int] = mapped_column(Integer, default=9)
    auto_send_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    live_sync_interval_seconds: Mapped[int] = mapped_column(Integer, default=900)


class TelegramChannel(TimestampMixin, Base):
    __tablename__ = "telegram_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    bot_token_encrypted: Mapped[str] = mapped_column(Text, default="")
    admin_chat_id_encrypted: Mapped[str] = mapped_column(Text, default="")
    admin_username: Mapped[str] = mapped_column(String(255), default="")
    last_test_status: Mapped[str] = mapped_column(Text, default="")
    last_test_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class ReportSnapshot(TimestampMixin, Base):
    __tablename__ = "report_snapshots"
    __table_args__ = (UniqueConstraint("tenant_id", "report_date", name="uq_report_snapshot_tenant_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    report_date: Mapped[dt.date] = mapped_column(Date, index=True)
    timezone: Mapped[str] = mapped_column(String(128))
    config_version: Mapped[int] = mapped_column(Integer, default=1)
    config_hash: Mapped[str] = mapped_column(String(128), default="")
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    rendered_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="built")
    error_message: Mapped[str] = mapped_column(Text, default="")
    source_window_start: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    source_window_end: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class DeliveryLog(TimestampMixin, Base):
    __tablename__ = "delivery_logs"
    __table_args__ = (Index("ix_delivery_tenant_status_created", "tenant_id", "status", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("report_snapshots.id", ondelete="SET NULL"))
    channel: Mapped[str] = mapped_column(String(32), default="telegram")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str] = mapped_column(String(255), default="", index=True)


class CallNoteCache(TimestampMixin, Base):
    __tablename__ = "call_note_cache"
    __table_args__ = (UniqueConstraint("tenant_id", "entity_type", "entity_id", "note_id", name="uq_call_note"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[int] = mapped_column(BigInteger)
    note_id: Mapped[int] = mapped_column(BigInteger)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)


class SyncState(TimestampMixin, Base):
    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, index=True)
    last_events_sync_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    last_tasks_sync_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str] = mapped_column(Text, default="")
    next_sync_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class EventInbox(Base):
    __tablename__ = "event_inbox"
    __table_args__ = (
        UniqueConstraint("source", "dedup_key", name="uq_event_inbox_source_dedup"),
        Index("ix_event_inbox_tenant_status_received", "tenant_id", "status", "received_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), index=True)
    source: Mapped[str] = mapped_column(String(64))
    dedup_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="received")
    received_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str] = mapped_column(Text, default="")


class OAuthState(Base):
    __tablename__ = "oauth_states"
    __table_args__ = (
        UniqueConstraint("state_hash", name="uq_oauth_state_hash"),
        Index("ix_oauth_states_status_expires", "status", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    account_id_hint: Mapped[int | None] = mapped_column(BigInteger)
    subdomain_hint: Mapped[str] = mapped_column(String(255), default="")
    referer: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"
    __table_args__ = (Index("ix_security_audit_tenant_event_created", "tenant_id", "event_type", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), index=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="ok")
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
