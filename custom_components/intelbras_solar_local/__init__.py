"""The Intelbras Solar Local integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from intelbras_solar_local import IntelbrasSolarClient

from .const import (
    CONF_CO2_FACTOR,
    CONF_ENERGY_PRICE,
    CONF_INSTALLED_CAPACITY,
    CONF_SCAN_INTERVAL,
    CONF_UNIT,
    DEFAULT_CO2_FACTOR,
    DEFAULT_ENERGY_PRICE,
    DEFAULT_INSTALLED_CAPACITY,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT,
    DOMAIN,
)
from .coordinator import IntelbrasSolarCoordinator
from .services import async_setup_services

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type IntelbrasSolarConfigEntry = ConfigEntry[IntelbrasSolarCoordinator]

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the set_parameter action."""
    async_setup_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: IntelbrasSolarConfigEntry
) -> bool:
    """Set up Intelbras Solar Local from a config entry."""
    client = IntelbrasSolarClient(
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
        entry.data.get(CONF_UNIT, DEFAULT_UNIT),
        session=async_get_clientsession(hass),
    )
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = IntelbrasSolarCoordinator(hass, entry, client, scan_interval)
    opts = entry.options
    coordinator.energy_price = opts.get(CONF_ENERGY_PRICE, DEFAULT_ENERGY_PRICE)
    coordinator.installed_capacity = opts.get(
        CONF_INSTALLED_CAPACITY, DEFAULT_INSTALLED_CAPACITY
    )
    coordinator.co2_factor = opts.get(CONF_CO2_FACTOR, DEFAULT_CO2_FACTOR)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: IntelbrasSolarConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.client.async_close()
    return unload_ok
