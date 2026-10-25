"""Tests for the calculated plant sensors."""
from __future__ import annotations

from homeassistant.core import State
from homeassistant.util import dt as dt_util
from intelbras_solar_local import InverterStatus
from pytest_homeassistant_custom_component.common import (
    mock_restore_cache_with_extra_data,
)

P = "sensor.intelbras_solar_local_plant_"
PRICE = {"energy_price": 0.92}


async def test_savings_and_environment(hass, init_integration):
    await init_integration(options=PRICE)
    assert hass.states.get(P + "savings_today").state == "25.48"
    assert hass.states.get(P + "savings_this_month").state == "586.78"
    assert hass.states.get(P + "savings_this_year").state == "6354.35"
    assert hass.states.get(P + "total_savings").state == "14117.95"
    total = hass.states.get(P + "total_savings")
    assert total.attributes["unit_of_measurement"] == "BRL"
    assert hass.states.get(P + "co2_avoided").state == "5226.7"
    assert hass.states.get(P + "trees_saved").state == "5.23"
    assert hass.states.get(P + "coal_saved").state == "6138.2"
    assert hass.states.get(P + "energy_price").state == "0.92"


async def test_savings_unknown_without_price(hass, init_integration):
    await init_integration()
    assert hass.states.get(P + "total_savings").state == "unknown"
    assert hass.states.get(P + "energy_price").state == "unknown"


async def test_capacity_yield_and_utilization(hass, init_integration):
    await init_integration()
    assert hass.states.get(P + "installed_capacity").state == "5.0"
    assert hass.states.get(P + "specific_yield_today").state == "5.54"
    assert hass.states.get(P + "utilization").state == "45.3"


async def test_capacity_option_overrides_rating(hass, init_integration):
    await init_integration(options={"installed_capacity": 5.5})
    assert hass.states.get(P + "installed_capacity").state == "5.5"
    assert hass.states.get(P + "specific_yield_today").state == "5.04"


async def test_plant_status(hass, init_integration, make_status):
    await init_integration(status=make_status(fault_code=38))
    assert hass.states.get(P + "status").state == "fault"


async def test_plant_status_offline(hass, init_integration):
    await init_integration(status=InverterStatus(online=False))
    assert hass.states.get(P + "status").state == "offline"


async def test_peak_power_tracks_max(hass, init_integration, mock_client, make_status):
    _, coordinator = await init_integration()
    assert hass.states.get(P + "peak_power_today").state == "2265"
    mock_client.async_get_status.return_value = make_status(power_ac=3100)
    await coordinator.async_refresh()
    mock_client.async_get_status.return_value = make_status(power_ac=900)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(P + "peak_power_today").state == "3100"


async def test_peak_power_restored_same_day(hass, init_integration):
    state = State(P + "peak_power_today", "4100", last_changed=dt_util.utcnow())
    mock_restore_cache_with_extra_data(
        hass,
        [(state, {"native_value": 4100, "native_unit_of_measurement": "W"})],
    )
    await init_integration()
    assert hass.states.get(P + "peak_power_today").state == "4100"
