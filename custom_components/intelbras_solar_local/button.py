"""Buttons for the Intelbras Solar Local integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from intelbras_solar_local import IntelbrasSolarError

from . import IntelbrasSolarConfigEntry
from .const import DEVICE_DATALOGGER
from .entity import IntelbrasSolarEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IntelbrasSolarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the buttons."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            IntelbrasSolarSyncClock(coordinator, entry, "sync_clock"),
            IntelbrasSolarRebootDatalogger(
                coordinator, entry, "reboot_datalogger", DEVICE_DATALOGGER
            ),
        ]
    )


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
        self.coordinator.async_set_written(clock=now)


class IntelbrasSolarRebootDatalogger(IntelbrasSolarEntity, ButtonEntity):
    """Restart the WiNet-S; readings pause for about a minute."""

    _attr_translation_key = "reboot_datalogger"
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.async_reboot_datalogger()
        except IntelbrasSolarError as err:
            raise HomeAssistantError(f"Failed to reboot the datalogger: {err}") from err
