"""Tests for the inverter parameter entities, controls and set_parameter."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
import pytest

from custom_components.intelbras_solar_local.const import DOMAIN

N = "number.intelbras_solar_local_"
S = "switch.intelbras_solar_local_"
SEL = "select.intelbras_solar_local_"


async def _enable(hass, entry, *entity_ids):
    registry = er.async_get(hass)
    for entity_id in entity_ids:
        registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_parameter_entities_created(hass, init_integration):
    await init_integration()
    registry = er.async_get(hass)
    standby = hass.states.get(N + "connecting_time")
    assert standby.state == "20.0"
    assert standby.attributes["unit_of_measurement"] == "s"
    assert standby.attributes["min"] == 10 and standby.attributes["max"] == 900
    assert standby.attributes["register"] == 30091
    assert hass.states.get(S + "pid_recovery").state == "off"
    # Grid-code settings exist but ship disabled.
    for entity_id in (
        SEL + "over_frequency_derating_curve",
        SEL + "protection_level",
        N + "overvoltage_level_1_protection_value",
        N + "power_factor_setting",
        SEL + "reactive_power_mode",
    ):
        entry = registry.async_get(entity_id)
        assert entry is not None and entry.disabled_by is not None, entity_id
    # Total yield adjustment is action-only; unknown keys get a plain name.
    unique_ids = [e.unique_id for e in registry.entities.values()]
    assert not [u for u in unique_ids if u.endswith("_30070")]
    mystery = registry.async_get(N + "mystery_setting")
    assert mystery is not None and mystery.disabled_by is not None


async def test_write_number_rereads_group(hass, init_integration, mock_client):
    await init_integration()
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": N + "connecting_time", "value": 30},
        blocking=True,
    )
    param, value = mock_client.async_set_parameter.await_args.args
    assert (param.key, value) == ("standby_time", 30.0)
    assert mock_client.async_get_parameters.call_count >= 3


async def test_switch_writes_option(hass, init_integration, mock_client):
    await init_integration()
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": S + "pid_recovery"}, blocking=True
    )
    param, value = mock_client.async_set_parameter.await_args.args
    assert (param.key, value) == ("pid_night_repair", "enable")


async def test_write_error_surfaces(hass, init_integration, mock_client):
    await init_integration()
    mock_client.async_set_parameter.side_effect = ValueError("outside range")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": N + "connecting_time", "value": 5},
            blocking=True,
        )


async def test_protection_number_range_and_applies(hass, init_integration):
    entry, _ = await init_integration()
    entity_id = N + "overvoltage_level_3_tripping_time"
    await _enable(hass, entry, entity_id, SEL + "protection_level")
    trip = hass.states.get(entity_id)
    # Factory value 0.02 s is below the vendor minimum of 0.05 s.
    assert trip.state == "0.02" and trip.attributes["min"] == 0.02
    # Level 3 settings do not apply while the protection level is "two_level".
    assert trip.attributes["applies"] is False
    assert hass.states.get(SEL + "protection_level").state == "two_level"


async def test_set_parameter_action(hass, init_integration, mock_client):
    await init_integration()
    await hass.services.async_call(
        DOMAIN,
        "set_parameter",
        {"parameter": "30070", "value": 15400},
        blocking=True,
    )
    param, value = mock_client.async_set_parameter.await_args.args
    assert (param.key, value) == ("set_total_power", 15400.0)
    await hass.services.async_call(
        DOMAIN,
        "set_parameter",
        {"parameter": "over_frequency_drop_curve", "value": "cura_b"},
        blocking=True,
    )
    assert mock_client.async_set_parameter.await_args.args[1] == "cura_b"
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "set_parameter", {"parameter": "nope", "value": 1}, blocking=True
        )


async def test_reboot_button(hass, init_integration, mock_client):
    await init_integration()
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.intelbras_solar_local_datalogger_reboot"},
        blocking=True,
    )
    mock_client.async_reboot_datalogger.assert_awaited_once()


async def test_power_factor_and_reactive_mode(
    hass, init_integration, mock_client, make_status
):
    entry, _ = await init_integration(
        status=make_status(power_factor_setting=1.0, reactive_mode="power_factor")
    )
    await _enable(hass, entry, N + "power_factor_setting", SEL + "reactive_power_mode")
    assert hass.states.get(N + "power_factor_setting").state == "1.0"
    assert hass.states.get(SEL + "reactive_power_mode").state == "power_factor"
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": N + "power_factor_setting", "value": -0.95},
        blocking=True,
    )
    mock_client.async_set_power_factor.assert_awaited_with(-0.95)
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": SEL + "reactive_power_mode", "option": "off"},
        blocking=True,
    )
    mock_client.async_set_reactive_mode.assert_awaited_with("off")
