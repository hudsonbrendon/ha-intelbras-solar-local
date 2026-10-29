"""Select entities for the Intelbras Solar Local integration."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from intelbras_solar_local import IntelbrasSolarError

from .const import DOMAIN, REACTIVE_MODE_OPTIONS
from .entity import (
    IntelbrasSolarEntity,
    IntelbrasSolarParameterEntity,
    async_add_parameter_entities,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [IntelbrasSolarReactiveMode(coordinator, entry, "reactive_mode")]
    )
    async_add_parameter_entities(
        coordinator, entry, async_add_entities, "select", IntelbrasSolarParameterSelect
    )


class IntelbrasSolarReactiveMode(IntelbrasSolarEntity, SelectEntity):
    """Reactive power regulation mode (holding register 5035)."""

    _attr_translation_key = "reactive_mode"
    _attr_icon = "mdi:sine-wave"
    _attr_options = REACTIVE_MODE_OPTIONS
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.reactive_mode

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.client.async_set_reactive_mode(option)
        except (IntelbrasSolarError, ValueError) as err:
            raise HomeAssistantError(f"Failed to write to the inverter: {err}") from err
        self.coordinator.async_set_written(reactive_mode=option)


class IntelbrasSolarParameterSelect(IntelbrasSolarParameterEntity, SelectEntity):
    """An inverter parameter with a fixed list of options."""

    def __init__(self, coordinator, entry, param) -> None:
        super().__init__(coordinator, entry, param)
        self._attr_options = list(param.options)

    @property
    def current_option(self) -> str | None:
        param = self.parameter
        return param.option if param else None

    async def async_select_option(self, option: str) -> None:
        await self._async_write(option)
