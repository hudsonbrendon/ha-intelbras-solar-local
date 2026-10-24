"""Tests for the Intelbras Solar Local button."""
from __future__ import annotations

from datetime import datetime

ENTITY = "button.intelbras_solar_local_sync_inverter_clock"


async def test_sync_clock(
    hass, init_integration, mock_client, entity_registry_enabled_by_default
):
    await init_integration()
    await hass.services.async_call(
        "button", "press", {"entity_id": ENTITY}, blocking=True
    )
    (when,), _ = mock_client.async_set_clock.call_args
    assert isinstance(when, datetime)
    assert when.tzinfo is None and when.microsecond == 0
    clock = hass.states.get("sensor.intelbras_solar_local_inverter_clock").state
    assert clock == when.isoformat(sep=" ")
