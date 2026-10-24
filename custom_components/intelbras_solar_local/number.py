"""Number entities for the Intelbras Solar Local integration."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from intelbras_solar_local import IntelbrasSolarError

from .const import DOMAIN
from .entity import IntelbrasSolarEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IntelbrasSolarPowerLimit(coordinator, entry, "power_limit")])


class IntelbrasSolarPowerLimit(IntelbrasSolarEntity, NumberEntity):
    """Active power limit (% of nominal); applies while limitation is on."""

    _attr_translation_key = "power_limit"
    _attr_icon = "mdi:speedometer-medium"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.power_limit

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self.coordinator.client.async_set_power_limit(value)
        except IntelbrasSolarError as err:
            raise HomeAssistantError(f"Failed to write to the inverter: {err}") from err
        self.coordinator.async_set_written(power_limit=value)
