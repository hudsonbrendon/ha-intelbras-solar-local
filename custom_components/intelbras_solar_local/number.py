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
        [
            IntelbrasSolarPowerLimit(coordinator, entry, "power_limit"),
            IntelbrasSolarPowerFactor(coordinator, entry, "power_factor_setting"),
        ]
    )
    async_add_parameter_entities(
        coordinator, entry, async_add_entities, "number", IntelbrasSolarParameterNumber
    )


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


class IntelbrasSolarPowerFactor(IntelbrasSolarEntity, NumberEntity):
    """Fixed power factor; used while the reactive mode is "power_factor"."""

    _attr_translation_key = "power_factor_setting"
    _attr_icon = "mdi:angle-acute"
    _attr_native_min_value = -1
    _attr_native_max_value = 1
    _attr_native_step = 0.001
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.power_factor_setting

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self.coordinator.client.async_set_power_factor(value)
        except (IntelbrasSolarError, ValueError) as err:
            raise HomeAssistantError(f"Failed to write to the inverter: {err}") from err
        self.coordinator.async_set_written(power_factor_setting=value)


class IntelbrasSolarParameterNumber(IntelbrasSolarParameterEntity, NumberEntity):
    """A numeric inverter parameter."""

    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, entry, param) -> None:
        super().__init__(coordinator, entry, param)
        self._attr_native_step = 10**-param.accuracy if param.accuracy else 1
        self._attr_native_unit_of_measurement = param.unit

    @property
    def native_value(self) -> float | None:
        param = self.parameter
        return param.value if param and isinstance(param.value, float) else None

    # The vendor's ranges can exclude the factory value itself (a 0.02 s trip
    # time with a 0.05 s minimum), so the bounds stretch to include it.
    @property
    def native_min_value(self) -> float:
        param = self.parameter
        return min(self._known(param and param.minimum), default=0)

    @property
    def native_max_value(self) -> float:
        param = self.parameter
        return max(self._known(param and param.maximum), default=100)

    def _known(self, bound: float | None) -> list[float]:
        return [b for b in (bound, self.native_value) if b is not None]

    async def async_set_native_value(self, value: float) -> None:
        await self._async_write(value)
