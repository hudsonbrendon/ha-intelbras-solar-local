"""Tests for the datalogger extras, firmware and grid protection sensors."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.util import dt as dt_util
from intelbras_solar_local import InverterInfo, InverterStatus, WifiSignal

from custom_components.intelbras_solar_local import coordinator as coord_mod

D = "sensor.intelbras_solar_local_datalogger_"
INV = "sensor.intelbras_solar_local_"


async def test_datalogger_sensors(hass, init_integration):
    await init_integration()
    signal = hass.states.get(D + "wi_fi_signal")
    assert signal.state == "-36"
    assert signal.attributes["unit_of_measurement"] == "dBm"
    assert hass.states.get(D + "wi_fi_network").state == "CASA"
    assert hass.states.get(D + "firmware").state == "WIFI-SV300.001.03.P002"
    assert hass.states.get(D + "hardware_version").state == "M_WI-FI_V01_V01_A"
    assert hass.states.get(D + "cloud_server").state == "app.isolarcloud.com"
    assert hass.states.get(D + "last_record").state != "unknown"


async def test_inverter_firmware_efficiency_and_grid(hass, init_integration):
    await init_integration()
    arm = hass.states.get(INV + "arm_firmware")
    assert arm.state == "SUNSTONE-S_01011.01.39"
    assert arm.attributes["family"] == "ARM_SUNSTONE-S_V11_V01_A"
    dsp = hass.states.get(INV + "dsp_firmware")
    assert dsp.state == "SUNSTONE-S_03011.01.24"
    assert dsp.attributes["cpld_version"] == "SUNSTONE-S_08011.01.01"
    assert hass.states.get(INV + "inverter_efficiency").state == "94.1"
    grid = hass.states.get(INV + "grid_protection_levels")
    assert grid.state == "2"
    assert grid.attributes["overvoltage_single_protect_value"] == 268.8


async def test_slow_extras_are_throttled(hass, init_integration, mock_client):
    _, coordinator = await init_integration()
    assert mock_client.async_get_wifi_signal.await_count == 1
    await coordinator.async_refresh()
    assert mock_client.async_get_wifi_signal.await_count == 1

    later = dt_util.utcnow() + coord_mod.SLOW_EXTRAS_INTERVAL + timedelta(seconds=1)
    mock_client.async_get_wifi_signal.return_value = WifiSignal("CASA", -50)
    with _frozen(later):
        await coordinator.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
    assert mock_client.async_get_wifi_signal.await_count == 2
    assert coordinator.wifi_signal.rssi == -50


async def test_poll_does_not_wait_for_slow_extras(
    hass, init_integration, mock_client
):
    import asyncio

    _, coordinator = await init_integration()
    release = asyncio.Event()

    async def slow_scan():
        await release.wait()
        return WifiSignal("CASA", -40)

    mock_client.async_get_wifi_signal.side_effect = slow_scan
    later = dt_util.utcnow() + coord_mod.SLOW_EXTRAS_INTERVAL + timedelta(seconds=1)
    with _frozen(later):
        await asyncio.wait_for(coordinator.async_refresh(), 1)
        # A second poll while the scan still runs does not start another one.
        await asyncio.wait_for(coordinator.async_refresh(), 1)
    assert coordinator.wifi_signal.rssi == -36
    release.set()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.wifi_signal.rssi == -40
    assert hass.states.get(D + "wi_fi_signal").state == "-40"


async def test_extras_failure_keeps_previous_value(hass, init_integration, mock_client):
    from intelbras_solar_local import IntelbrasSolarConnectionError

    _, coordinator = await init_integration()
    mock_client.async_get_wifi_signal.side_effect = IntelbrasSolarConnectionError("x")
    later = dt_util.utcnow() + coord_mod.SLOW_EXTRAS_INTERVAL + timedelta(seconds=1)
    with _frozen(later):
        await coordinator.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
    assert coordinator.data.online is True
    assert coordinator.wifi_signal.rssi == -36


async def test_last_record_survives_night(hass, init_integration, mock_client):
    from intelbras_solar_local import IntelbrasSolarConnectionError

    _, coordinator = await init_integration()
    mock_client.async_get_status.side_effect = IntelbrasSolarConnectionError("x")
    for _ in range(3):
        await coordinator.async_refresh()
    await hass.async_block_till_done()
    last = hass.states.get(D + "last_record").state
    assert last not in ("unknown", STATE_UNAVAILABLE)
    assert hass.states.get(D + "wi_fi_signal").state == STATE_UNAVAILABLE


async def test_grid_levels_unknown_without_params(hass, init_integration, mock_client):
    mock_client.async_get_parameters.side_effect = lambda kind: []
    await init_integration(status=None)
    assert hass.states.get(INV + "grid_protection_levels").state == "unknown"
    _ = InverterStatus


def _frozen(when):
    from unittest.mock import patch

    return patch.object(coord_mod.dt_util, "utcnow", return_value=when)


async def test_firmware_falls_back_to_modbus(hass, init_integration, mock_client):
    mock_client.async_get_inverter_info.return_value = InverterInfo()
    await init_integration()
    arm = hass.states.get(INV + "arm_firmware")
    assert arm.state == "ARM_SUNSTONE-S_V11_V01_A"


async def test_fault_history_sensors(hass, init_integration):
    await hass.config.async_set_time_zone("America/Sao_Paulo")
    await init_integration()
    count = hass.states.get(INV + "recorded_faults")
    assert count.state == "2"
    by_fault = count.attributes["by_fault"]
    assert by_fault == {"grid_interruption": 1, "leakage_current": 1}
    assert len(count.attributes["recent"]) == 3
    last = hass.states.get(INV + "last_fault")
    # 11:46:35 in São Paulo (UTC-3) is 14:46:35 UTC.
    assert last.state == "2026-09-18T14:46:35+00:00"
    assert last.attributes["fault"] == "grid_interruption"


async def test_last_fault_unknown_without_history(hass, init_integration, mock_client):
    mock_client.async_get_fault_history.return_value = []
    await init_integration()
    assert hass.states.get(INV + "last_fault").state == "unknown"
    assert hass.states.get(INV + "recorded_faults").state == "0"


async def test_unread_history_is_unknown_and_retried_soon(
    hass, init_integration, mock_client
):
    from intelbras_solar_local import IntelbrasSolarConnectionError

    mock_client.async_get_fault_history.side_effect = IntelbrasSolarConnectionError("x")
    _, coordinator = await init_integration()
    assert hass.states.get(INV + "recorded_faults").state == "unknown"

    mock_client.async_get_fault_history.side_effect = None
    soon = dt_util.utcnow() + coord_mod.SLOW_EXTRAS_RETRY + timedelta(seconds=1)
    with _frozen(soon):
        await coordinator.async_refresh()
        await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(INV + "recorded_faults").state == "2"
