"""Binary sensors for the Intelbras Solar Local integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from intelbras_solar_local import InverterStatus

from .const import DOMAIN
from .entity import IntelbrasSolarEntity


@dataclass(frozen=True, kw_only=True)
class IntelbrasSolarBinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[InverterStatus], bool | None]
    attrs_fn: Callable[[InverterStatus], dict[str, Any]] | None = None
    always_available: bool = False


BINARY_SENSORS: tuple[IntelbrasSolarBinarySensorEntityDescription, ...] = (
    IntelbrasSolarBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda s: s.online,
        always_available=True,
    ),
    IntelbrasSolarBinarySensorEntityDescription(
        key="producing",
        translation_key="producing",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda s: s.producing,
    ),
    IntelbrasSolarBinarySensorEntityDescription(
        key="fault",
        translation_key="fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda s: s.has_fault,
        attrs_fn=lambda s: {
            "fault_code": s.fault_code,
            "faults": s.datalogger.faults if s.datalogger else [],
        },
    ),
    IntelbrasSolarBinarySensorEntityDescription(
        key="datalogger_wifi",
        translation_key="datalogger_wifi",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.datalogger.wifi_connected if s.datalogger else None,
    ),
    IntelbrasSolarBinarySensorEntityDescription(
        key="datalogger_cloud",
        translation_key="datalogger_cloud",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.datalogger.cloud_connected if s.datalogger else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        IntelbrasSolarBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class IntelbrasSolarBinarySensor(IntelbrasSolarEntity, BinarySensorEntity):
    """A boolean state of the inverter or datalogger."""

    entity_description: IntelbrasSolarBinarySensorEntityDescription

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if self.entity_description.always_available:
            return self.coordinator.last_update_success
        return super().available

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
