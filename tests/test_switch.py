"""Tests for the Intelbras Solar Local switches."""
from __future__ import annotations

import pytest
from homeassistant.const import STATE_ON
from homeassistant.exceptions import HomeAssistantError
from intelbras_solar_local import IntelbrasSolarConnectionError

P = "switch.intelbras_solar_local_"


async def test_switches_disabled_by_default(hass, init_integration):
    await init_integration()
    assert hass.states.get(P + "inverter_on") is None


async def test_switches_write_inverter(
    hass, init_integration, mock_client, entity_registry_enabled_by_default
):
    await init_integration()
    assert hass.states.get(P + "inverter_on").state == STATE_ON
    assert hass.states.get(P + "power_limitation").state == STATE_ON

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": P + "inverter_on"}, blocking=True
    )
    mock_client.async_set_inverter_on.assert_awaited_once_with(False)
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": P + "power_limitation"}, blocking=True
    )
    mock_client.async_set_power_limit_enabled.assert_awaited_once_with(True)


async def test_switch_write_error(
    hass, init_integration, mock_client, entity_registry_enabled_by_default
):
    await init_integration()
    mock_client.async_set_inverter_on.side_effect = IntelbrasSolarConnectionError("x")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": P + "inverter_on"}, blocking=True
        )
