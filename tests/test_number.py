"""Tests for the Intelbras Solar Local number entity."""
from __future__ import annotations

import pytest
from homeassistant.exceptions import HomeAssistantError
from intelbras_solar_local import IntelbrasSolarProtocolError

ENTITY = "number.intelbras_solar_local_power_limit"


async def test_power_limit(
    hass, init_integration, mock_client, entity_registry_enabled_by_default
):
    await init_integration()
    state = hass.states.get(ENTITY)
    assert state.state == "100.0"
    assert state.attributes["unit_of_measurement"] == "%"

    await hass.services.async_call(
        "number", "set_value", {"entity_id": ENTITY, "value": 80}, blocking=True
    )
    mock_client.async_set_power_limit.assert_awaited_once_with(80.0)
    assert hass.states.get(ENTITY).state == "80.0"


async def test_power_limit_write_error(
    hass, init_integration, mock_client, entity_registry_enabled_by_default
):
    await init_integration()
    mock_client.async_set_power_limit.side_effect = IntelbrasSolarProtocolError("x")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "number", "set_value", {"entity_id": ENTITY, "value": 50}, blocking=True
        )
    assert hass.states.get(ENTITY).state == "100.0"
