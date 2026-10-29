"""Shared fixtures for the Intelbras Solar Local tests."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from intelbras_solar_local import (
    PARAM_PROTECTION,
    PARAM_SYSTEM,
    DataloggerInfo,
    DataloggerStatus,
    FaultEvent,
    InverterInfo,
    InverterStatus,
    Mppt,
    Parameter,
    WifiSignal,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.intelbras_solar_local.const import DOMAIN

SERIAL = "XS123456780"
ENTRY_DATA = {
    "name": "Intelbras Solar Local",
    "host": "192.168.31.17",
    "port": 502,
    "unit": 1,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""
    yield


@pytest.fixture(autouse=True)
def mock_clientsession():
    """Replace async_get_clientsession with a fake to avoid lingering threads."""
    session = MagicMock()
    with patch(
        "custom_components.intelbras_solar_local.async_get_clientsession",
        return_value=session,
    ), patch(
        "custom_components.intelbras_solar_local.config_flow.async_get_clientsession",
        return_value=session,
    ):
        yield session


@pytest.fixture
def entity_registry_enabled_by_default():
    """Enable entities that ship disabled (controls, clock), like HA core does."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
        new_callable=PropertyMock,
    ):
        yield


@pytest.fixture
def make_status():
    """Factory for a fully-populated InverterStatus, overridable per test."""

    def _make(**overrides) -> InverterStatus:
        defaults = dict(
            online=True,
            serial=SERIAL,
            device_type_code=0x2614,
            nominal_power=5.0,
            energy_today=27.7,
            energy_month=637.8,
            energy_year=6906.9,
            energy_total=15345.6,
            running_hours_total=7262,
            running_minutes_today=578,
            temperature=64.5,
            power_ac=2265,
            power_dc=2408,
            power_apparent=2265,
            power_reactive=-4,
            power_factor=1.0,
            grid_voltage=231.0,
            grid_current=9.7,
            grid_frequency=60.06,
            bus_voltage=377.0,
            insulation_resistance=1663,
            work_state_code=0,
            fault_code=0,
            inverter_on=True,
            power_limit_enabled=True,
            power_limit=100.0,
            clock=datetime(2026, 10, 24, 14, 51, 39),
            mppts=[Mppt(189.0, 6.2), Mppt(186.0, 6.5)],
            arm_firmware="ARM_SUNSTONE-S_V11_V01_A",
            dsp_firmware="MDSP_SUNSTONE-S_V11_V01_A",
            datalogger=DataloggerStatus(
                model="IONS-5K M5",
                wifi_connected=True,
                cloud_connected=False,
                total_faults=0,
                total_alarms=1,
            ),
        )
        defaults.update(overrides)
        return InverterStatus(**defaults)

    return _make


@pytest.fixture
def mock_client():
    """Patch every IntelbrasSolarClient method the integration calls."""
    base = "intelbras_solar_local.client.IntelbrasSolarClient"
    names = (
        "async_get_status",
        "async_get_inverter_data",
        "async_set_inverter_on",
        "async_set_power_limit_enabled",
        "async_set_power_limit",
        "async_set_clock",
        "async_close",
        "async_get_datalogger_info",
        "async_get_wifi_signal",
        "async_get_grid_parameters",
        "async_get_inverter_info",
        "async_get_fault_history",
        "async_get_parameters",
        "async_set_parameter",
        "async_reboot_datalogger",
        "async_set_power_factor",
        "async_set_reactive_mode",
    )
    patchers = {n: patch(f"{base}.{n}", new=AsyncMock()) for n in names}
    mocks = {n: p.start() for n, p in patchers.items()}
    mocks["async_get_datalogger_info"].return_value = DataloggerInfo(
        serial="B12345",
        firmware_version="WIFI-SV300.001.03.P002",
        build_version="WIFI-SV300.001.03.B000",
        hardware_version="M_WI-FI_V01_V01_A",
        cloud_server="app.isolarcloud.com",
        timezone="UTC-03:00",
        wifi_connected=True,
        ethernet_connected=False,
    )
    mocks["async_get_wifi_signal"].return_value = WifiSignal("CASA", -36)
    mocks["async_get_inverter_info"].return_value = InverterInfo(
        serial=SERIAL,
        model="IONS-5K M5",
        rated_power=5.0,
        rated_reactive_power=3.0,
        arm_version="SUNSTONE-S_01011.01.39",
        mdsp_version="SUNSTONE-S_03011.01.24",
        sdsp_version="SUNSTONE-S_04011.01.01",
        cpld_version="SUNSTONE-S_08011.01.01",
    )
    mocks["async_get_fault_history"].return_value = [
        FaultEvent(datetime(*when), code, name, "fault", raised, "10")
        for when, code, name, raised in (
            ((2026, 9, 18, 11, 46, 45), 5, "grid_interruption", False),
            ((2026, 9, 18, 11, 46, 35), 5, "grid_interruption", True),
            ((2026, 8, 7, 15, 41, 57), 6, "leakage_current", True),
        )
    ]
    on_off = {"enable": "170", "prohibited": "85"}
    levels = {"single": "0", "two_level": "1", "three_level": "2"}
    params = {
        PARAM_SYSTEM: [
            Parameter("standby_time", 20.0, "s", 30091, PARAM_SYSTEM, 2, 0, 10, 900),
            Parameter("pid_night_repair", 85.0, None, 30310, PARAM_SYSTEM, 5,
                      options=on_off),
            Parameter("over_frequency_drop_curve", 0.0, None, 31413, PARAM_SYSTEM,
                      14, options={"cura_a": "0", "cura_b": "1"}),
            Parameter("set_total_power", 0.0, "kWh", 30070, PARAM_SYSTEM, 1, 0,
                      -200000000, 200000000),
            Parameter("mystery_setting", 3.0, None, 39999, PARAM_SYSTEM, 99, 0, 0, 9),
        ],
        PARAM_PROTECTION: [
            Parameter("protection_series", 1.0, None, 32313, PARAM_PROTECTION, 1,
                      options=levels),
            Parameter("overvoltage_single_protect_value", 268.8, "V", 32323,
                      PARAM_PROTECTION, 7, 1, 240.2, 336.0, levels=[0, 1, 2]),
            Parameter("overvoltage_level3_protect_time", 0.02, "s", 32380,
                      PARAM_PROTECTION, 35, 2, 0.05, 14400.0, levels=[2, 3, 4]),
        ],
    }
    mocks["async_get_parameters"].side_effect = lambda kind: params[kind]
    yield MagicMock(**mocks)
    for p in patchers.values():
        p.stop()


@pytest.fixture
def init_integration(hass, make_status, mock_client):
    """Set up the integration with a patched client. Returns (entry, coordinator)."""

    async def _init(status=None, options=None):
        mock_client.async_get_status.return_value = (
            make_status() if status is None else status
        )
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Intelbras Solar Local",
            data=ENTRY_DATA,
            unique_id=SERIAL,
            entry_id="intelbras_test",
            options=options or {},
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        return entry, hass.data[DOMAIN][entry.entry_id]

    return _init
