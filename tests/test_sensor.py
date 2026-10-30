"""Tests for the Intelbras Solar Local sensors."""

from __future__ import annotations

from homeassistant.const import STATE_UNAVAILABLE
from intelbras_solar_local import InverterStatus

P = "sensor.intelbras_solar_local_"


async def test_sensors_report_status(hass, init_integration):
    await init_integration()
    expected = {
        "ac_power": "2265",
        "dc_power": "2408",
        "apparent_power": "2265",
        "reactive_power": "-4",
        "power_factor": "1.0",
        "energy_today": "27.7",
        "energy_this_month": "637.8",
        "energy_this_year": "6906.9",
        "total_energy": "15345.6",
        "mppt1_power": "1172",
        "mppt1_voltage": "189.0",
        "mppt1_current": "6.2",
        "mppt2_power": "1209",
        "mppt2_voltage": "186.0",
        "mppt2_current": "6.5",
        "grid_voltage": "231.0",
        "grid_current": "9.7",
        "grid_frequency": "60.06",
        "internal_temperature": "64.5",
        "work_state": "running",
        "bus_voltage": "377.0",
        "insulation_resistance": "1663",
        "fault_code": "0",
        "active_alarms": "1",
        "running_time_today": "578",
        "total_running_time": "7262",
        "nominal_power": "5.0",
    }
    for suffix, value in expected.items():
        state = hass.states.get(P + suffix)
        assert state is not None, suffix
        assert state.state == value, (suffix, state.state)


async def test_energy_sensor_attributes(hass, init_integration):
    await init_integration()
    state = hass.states.get(P + "total_energy")
    assert state.attributes["unit_of_measurement"] == "kWh"
    assert state.attributes["device_class"] == "energy"
    assert state.attributes["state_class"] == "total_increasing"


async def test_work_state_options_cover_every_state(
    hass, init_integration, make_status
):
    await init_integration(status=make_status(work_state_code=0x1234))
    state = hass.states.get(P + "work_state")
    assert state.state == "unknown"
    assert "fault" in state.attributes["options"]


async def test_sensors_unavailable_while_asleep(hass, init_integration):
    await init_integration(status=InverterStatus(online=False))
    assert hass.states.get(P + "ac_power").state == STATE_UNAVAILABLE
    assert hass.states.get(P + "energy_today").state == STATE_UNAVAILABLE


async def test_alarms_unknown_without_datalogger(hass, init_integration, make_status):
    await init_integration(status=make_status(datalogger=None, mppts=[]))
    assert hass.states.get(P + "active_alarms").state == "unknown"
    assert hass.states.get(P + "mppt1_power").state == "unknown"


async def test_clock_sensor_disabled_by_default(hass, init_integration):
    await init_integration()
    assert hass.states.get(P + "inverter_clock") is None


async def test_clock_sensor(hass, init_integration, entity_registry_enabled_by_default):
    await init_integration()
    assert hass.states.get(P + "inverter_clock").state == "2026-10-24 14:51:39"
