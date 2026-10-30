"""Tests for the inverter / datalogger / plant device split."""

from __future__ import annotations

from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.intelbras_solar_local.const import DOMAIN

from .conftest import SERIAL


async def test_three_devices(hass, init_integration):
    entry, _ = await init_integration()
    devices = dr.async_get(hass)
    inverter = devices.async_get_device_by_identifier((DOMAIN, SERIAL), entry.entry_id)
    datalogger = devices.async_get_device_by_identifier(
        (DOMAIN, f"{SERIAL}_datalogger"), entry.entry_id
    )
    plant = devices.async_get_device_by_identifier(
        (DOMAIN, f"{SERIAL}_plant"), entry.entry_id
    )

    assert inverter.sw_version == "SUNSTONE-S_01011.01.39"
    assert datalogger.name == "Intelbras Solar Local Datalogger"
    assert datalogger.model == "WiNet-S"
    assert datalogger.serial_number == "B12345"
    assert datalogger.sw_version == "WIFI-SV300.001.03.P002"
    assert datalogger.hw_version == "M_WI-FI_V01_V01_A"
    assert plant.name == "Intelbras Solar Local Plant"

    entities = er.async_get(hass)
    wifi = entities.async_get("binary_sensor.intelbras_solar_local_datalogger_wi_fi")
    assert wifi.device_id == datalogger.id
    savings = entities.async_get("sensor.intelbras_solar_local_plant_total_savings")
    assert savings.device_id == plant.id
