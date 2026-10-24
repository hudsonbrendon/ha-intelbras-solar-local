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


def _zeroconf_info(host="192.168.31.17"):
    from types import SimpleNamespace

    # async_step_zeroconf is duck-typed on host, so a lightweight stand-in
    # avoids importing homeassistant.components.zeroconf in CI.
    return SimpleNamespace(
        host=host,
        name="WiNet-WebServer._http._tcp.local.",
        properties={"board": "WiNet-S", "path": "/"},
    )


async def test_zeroconf_discovery_confirms_and_creates_entry(
    hass, mock_client, make_status
):
    mock_client.async_get_inverter_data.return_value = make_status()
    mock_client.async_get_status.return_value = make_status()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=_zeroconf_info(),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["description_placeholders"] == {
        "host": "192.168.31.17",
        "model": "IONS-5K M5",
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Telhado"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Telhado"
    assert result["data"] == {**ENTRY_DATA, "name": "Telhado"}
    assert result["result"].unique_id == SERIAL


async def test_zeroconf_updates_host_of_known_inverter(
    hass, init_integration, mock_client, make_status
):
    entry, _ = await init_integration()
    mock_client.async_get_inverter_data.return_value = make_status()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=_zeroconf_info("192.168.31.88"),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "192.168.31.88"


async def test_zeroconf_same_host_aborts_without_probe(
    hass, init_integration, mock_client
):
    await init_integration()
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=_zeroconf_info(),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_client.async_get_inverter_data.assert_not_awaited()


async def test_zeroconf_unreachable_inverter_aborts(hass, mock_client):
    mock_client.async_get_inverter_data.side_effect = IntelbrasSolarConnectionError(
        "asleep"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=_zeroconf_info(),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


def test_zeroconf_matcher_targets_winet_only():
    """The real WiNet-S announces WiNet-WebServer._http._tcp with board=WiNet-S;
    plain _http._tcp devices must not raise a discovery card."""
    import json
    from fnmatch import fnmatch
    from pathlib import Path

    manifest = json.loads(
        (
            Path(__file__).parent.parent
            / "custom_components"
            / "intelbras_solar_local"
            / "manifest.json"
        ).read_text()
    )
    (matcher,) = manifest["zeroconf"]

    def matches(name: str, board: str | None) -> bool:
        return (
            fnmatch(name.lower(), matcher["name"])
            and (board or "").lower() == matcher["properties"]["board"]
        )

    assert matcher["type"] == "_http._tcp.local."
    assert matches("WiNet-WebServer._http._tcp.local.", "WiNet-S")
    assert not matches("Brother printer._http._tcp.local.", None)
    assert not matches("WiNet-WebServer._http._tcp.local.", "other")
