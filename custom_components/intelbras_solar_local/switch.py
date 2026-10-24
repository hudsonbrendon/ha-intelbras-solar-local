"""Switches for the Intelbras Solar Local integration.

They write holding registers on the inverter, so they ship disabled.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from intelbras_solar_local import (
    IntelbrasSolarClient,
    IntelbrasSolarError,
    InverterStatus,
)

from .const import DOMAIN
from .entity import IntelbrasSolarEntity


@dataclass(frozen=True, kw_only=True)
class IntelbrasSolarSwitchEntityDescription(SwitchEntityDescription):
    field: str
    value_fn: Callable[[InverterStatus], bool | None]
    set_fn: Callable[[IntelbrasSolarClient, bool], Awaitable[None]]


SWITCHES: tuple[IntelbrasSolarSwitchEntityDescription, ...] = (
    IntelbrasSolarSwitchEntityDescription(
        key="inverter_on",
        translation_key="inverter_on",
        icon="mdi:power",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        field="inverter_on",
        value_fn=lambda s: s.inverter_on,
        set_fn=lambda c, on: c.async_set_inverter_on(on),
    ),
    IntelbrasSolarSwitchEntityDescription(
        key="power_limit_enabled",
        translation_key="power_limit_enabled",
        icon="mdi:speedometer",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
        field="power_limit_enabled",
        value_fn=lambda s: s.power_limit_enabled,
        set_fn=lambda c, on: c.async_set_power_limit_enabled(on),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        IntelbrasSolarSwitch(coordinator, entry, description)
        for description in SWITCHES
    )


class IntelbrasSolarSwitch(IntelbrasSolarEntity, SwitchEntity):
    """An on/off setting written to the inverter."""

    entity_description: IntelbrasSolarSwitchEntityDescription

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set(False)

    async def _async_set(self, value: bool) -> None:
        try:
            await self.entity_description.set_fn(self.coordinator.client, value)
        except IntelbrasSolarError as err:
            raise HomeAssistantError(f"Failed to write to the inverter: {err}") from err
        self.coordinator.async_set_written(**{self.entity_description.field: value})
