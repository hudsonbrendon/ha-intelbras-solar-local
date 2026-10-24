"""Tests for the coordinator."""
from __future__ import annotations

from intelbras_solar_local import (
    IntelbrasSolarConnectionError,
    IntelbrasSolarProtocolError,
)


async def test_unreachable_inverter_becomes_offline(
    hass, init_integration, mock_client
):
    _, coordinator = await init_integration()
    mock_client.async_get_status.side_effect = IntelbrasSolarConnectionError("down")
    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    assert coordinator.data.online is False

    mock_client.async_get_status.side_effect = IntelbrasSolarProtocolError("exc 4")
    await coordinator.async_refresh()
    assert coordinator.data.online is False


async def test_recovers_when_inverter_wakes(
    hass, init_integration, mock_client, make_status
):
    _, coordinator = await init_integration()
    mock_client.async_get_status.side_effect = IntelbrasSolarConnectionError("down")
    await coordinator.async_refresh()
    mock_client.async_get_status.side_effect = None
    mock_client.async_get_status.return_value = make_status(power_ac=10)
    await coordinator.async_refresh()
    assert coordinator.data.online is True
    assert coordinator.data.power_ac == 10
