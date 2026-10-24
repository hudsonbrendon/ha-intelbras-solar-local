"""Tests for the coordinator."""
from __future__ import annotations

from unittest.mock import patch

from intelbras_solar_local import (
    IntelbrasSolarConnectionError,
    IntelbrasSolarProtocolError,
)

from custom_components.intelbras_solar_local import coordinator as coord_mod


async def test_offline_only_after_consecutive_failures(
    hass, init_integration, mock_client
):
    _, coordinator = await init_integration()
    mock_client.async_get_status.side_effect = IntelbrasSolarConnectionError("down")
    await coordinator.async_refresh()
    await coordinator.async_refresh()
    assert coordinator.data.online is True  # two blips keep the last reading
    assert coordinator.data.power_ac == 2265

    mock_client.async_get_status.side_effect = IntelbrasSolarProtocolError("exc 4")
    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    assert coordinator.data.online is False


async def test_recovers_when_inverter_wakes(
    hass, init_integration, mock_client, make_status
):
    _, coordinator = await init_integration()
    mock_client.async_get_status.side_effect = IntelbrasSolarConnectionError("down")
    for _ in range(3):
        await coordinator.async_refresh()
    assert coordinator.data.online is False
    mock_client.async_get_status.side_effect = None
    mock_client.async_get_status.return_value = make_status(power_ac=10)
    await coordinator.async_refresh()
    assert coordinator.data.online is True
    assert coordinator.data.power_ac == 10


async def test_failure_counter_resets_on_success(hass, init_integration, mock_client):
    _, coordinator = await init_integration()
    status = mock_client.async_get_status.return_value
    for _ in range(3):
        mock_client.async_get_status.side_effect = IntelbrasSolarConnectionError("x")
        await coordinator.async_refresh()
        await coordinator.async_refresh()
        mock_client.async_get_status.side_effect = None
        mock_client.async_get_status.return_value = status
        await coordinator.async_refresh()
        assert coordinator.data.online is True


async def test_written_fields_survive_stale_poll(hass, init_integration, mock_client):
    _, coordinator = await init_integration()
    coordinator.async_set_written(power_limit=80.0)
    # A poll right after the write still reads the old register (100 %).
    await coordinator.async_refresh()
    assert coordinator.data.power_limit == 80.0

    with patch.object(coord_mod.time, "monotonic", return_value=1e12):
        mock_client.async_get_status.return_value.power_limit = 80.0
        await coordinator.async_refresh()
    assert coordinator.data.power_limit == 80.0
    assert coordinator._written == {}
