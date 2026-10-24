"""Buttons for the Intelbras Solar Local integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from intelbras_solar_local import IntelbrasSolarError

from .const import DOMAIN
from .entity import IntelbrasSolarEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IntelbrasSolarSyncClock(coordinator, entry, "sync_clock")])


class IntelbrasSolarSyncClock(IntelbrasSolarEntity, ButtonEntity):
    """Set the inverter clock to Home Assistant's local time."""

    _attr_translation_key = "sync_clock"
    _attr_icon = "mdi:clock-check-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    async def async_press(self) -> None:
        now = dt_util.now().replace(tzinfo=None, microsecond=0)
        try:
            await self.coordinator.client.async_set_clock(now)
        except IntelbrasSolarError as err:
            raise HomeAssistantError(f"Failed to write to the inverter: {err}") from err
        await self.coordinator.async_request_refresh()
