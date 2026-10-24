"""Tests for the Intelbras Solar Local binary sensors."""
from __future__ import annotations

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from intelbras_solar_local import DataloggerStatus, InverterStatus

P = "binary_sensor.intelbras_solar_local_"


async def test_binary_sensors_report_status(hass, init_integration):
    await init_integration()
    assert hass.states.get(P + "online").state == STATE_ON
    assert hass.states.get(P + "producing").state == STATE_ON
    assert hass.states.get(P + "fault").state == STATE_OFF
    assert hass.states.get(P + "datalogger_wi_fi").state == STATE_ON
    assert hass.states.get(P + "datalogger_cloud").state == STATE_OFF


async def test_fault_reports_code_and_list(hass, init_integration, make_status):
    faults = [{"dev_name": "IONS-5K M5", "fault_code": "38"}]
    status = make_status(
        work_state_code=0x5500,
        fault_code=38,
        datalogger=DataloggerStatus(total_faults=1, faults=faults),
    )
    await init_integration(status=status)
    state = hass.states.get(P + "fault")
    assert state.state == STATE_ON
    assert state.attributes["fault_code"] == 38
    assert state.attributes["faults"] == faults
    assert hass.states.get(P + "producing").state == STATE_OFF


async def test_online_stays_available_while_asleep(hass, init_integration):
    await init_integration(status=InverterStatus(online=False))
    assert hass.states.get(P + "online").state == STATE_OFF
    assert hass.states.get(P + "producing").state == STATE_UNAVAILABLE
