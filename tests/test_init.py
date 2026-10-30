"""Tests for integration setup/unload."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from intelbras_solar_local import InverterStatus

from custom_components.intelbras_solar_local.const import DOMAIN

from .conftest import SERIAL


async def test_setup_and_unload(hass, init_integration, mock_client):
    entry, coordinator = await init_integration()
    assert entry.state is ConfigEntryState.LOADED
    assert coordinator.data.online is True

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, SERIAL), entry.entry_id
    )
    assert device.model == "IONS-5K M5"
    assert device.serial_number == SERIAL
    assert device.configuration_url == "http://192.168.31.17"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    mock_client.async_close.assert_awaited()


async def test_setup_while_inverter_asleep(hass, init_integration):
    entry, coordinator = await init_integration(status=InverterStatus(online=False))
    assert entry.state is ConfigEntryState.LOADED
    assert coordinator.data.online is False


async def test_options_change_reloads(hass, init_integration, mock_client):
    entry, _ = await init_integration()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 30}
    )
    await hass.async_block_till_done()
    assert entry.runtime_data.update_interval.total_seconds() == 30
