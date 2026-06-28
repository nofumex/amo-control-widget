from __future__ import annotations

import pytest
from app.reports.schemas import ReportConfigSchema
from pydantic import ValidationError


def test_settings_validation_bounds() -> None:
    with pytest.raises(ValidationError):
        ReportConfigSchema(work_session_gap_minutes=181)
    with pytest.raises(ValidationError):
        ReportConfigSchema(build_hour=24)


def test_tenant_isolation_selected_users() -> None:
    tenant_a = ReportConfigSchema(selected_user_ids=[1])
    tenant_b = ReportConfigSchema(selected_user_ids=[2])
    assert tenant_a.selected_user_ids == [1]
    assert tenant_b.selected_user_ids == [2]
