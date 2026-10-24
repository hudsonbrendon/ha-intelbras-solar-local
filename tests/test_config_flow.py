"""Tests for the config and options flows."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from intelbras_solar_local import IntelbrasSolarConnectionError

from custom_components.intelbras_solar_local.const import DOMAIN

from .conftest import ENTRY_DATA, SERIAL


async def test_user_flow_creates_entry(hass, mock_client, make_status):
    mock_client.async_get_inverter_data.return_value = make_status()
    mock_client.async_get_status.return_value = make_status()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ENTRY_DATA
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Intelbras Solar Local"
    assert result["data"] == ENTRY_DATA
    assert result["result"].unique_id == SERIAL
    mock_client.async_close.assert_awaited()


async def test_user_flow_cannot_connect(hass, mock_client):
    mock_client.async_get_inverter_data.side_effect = IntelbrasSolarConnectionError(
        "down"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ENTRY_DATA
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_already_configured_updates_host(
    hass, init_integration, mock_client, make_status
):
    entry, _ = await init_integration()
    mock_client.async_get_inverter_data.return_value = make_status()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, "host": "192.168.31.99"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "192.168.31.99"


async def test_options_flow(hass, init_integration):
    entry, _ = await init_integration()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 60}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"scan_interval": 60}
