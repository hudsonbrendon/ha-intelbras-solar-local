"""Tests for diagnostics."""
from __future__ import annotations

from custom_components.intelbras_solar_local.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_redacts_serial(hass, init_integration):
    entry, _ = await init_integration()
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["entry"]["data"]["host"] == "192.168.31.17"
    assert diag["status"]["serial"] == "**REDACTED**"
    assert diag["status"]["power_ac"] == 2265
    assert diag["derived"] == {
        "model": "IONS-5K M5",
        "work_state": "running",
        "producing": True,
        "has_fault": False,
    }
