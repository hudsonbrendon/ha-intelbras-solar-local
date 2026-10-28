"""Base entity for the Intelbras Solar Local integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEVICE_DATALOGGER,
    DEVICE_INVERTER,
    DEVICE_PLANT,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import IntelbrasSolarCoordinator


def device_info(
    coordinator: IntelbrasSolarCoordinator, entry: ConfigEntry, kind: str
) -> DeviceInfo:
    """Inverter, datalogger and plant devices, like the Intelbras cloud splits them.

    The inverter keeps the serial-only identifier it had before the split, so
    existing entities stay on it.
    """
    serial = entry.unique_id or entry.entry_id
    url = f"http://{coordinator.client.host}"
    data = coordinator.data
    if kind == DEVICE_DATALOGGER:
        info = coordinator.datalogger_info
        return DeviceInfo(
            identifiers={(DOMAIN, f"{serial}_datalogger")},
            translation_key=DEVICE_DATALOGGER,
            translation_placeholders={"name": entry.title},
            manufacturer=MANUFACTURER,
            model="WiNet-S",
            serial_number=info.serial if info else None,
            sw_version=info.firmware_version if info else None,
            hw_version=info.hardware_version if info else None,
            configuration_url=url,
        )
    if kind == DEVICE_PLANT:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{serial}_plant")},
            translation_key=DEVICE_PLANT,
            translation_placeholders={"name": entry.title},
            manufacturer=MANUFACTURER,
            model="Solar plant",
        )
    return DeviceInfo(
        identifiers={(DOMAIN, serial)},
        name=entry.title,
        manufacturer=MANUFACTURER,
        model=data.model if data else None,
        serial_number=entry.unique_id,
        sw_version=_arm_version(coordinator),
        configuration_url=url,
        via_device=(DOMAIN, f"{serial}_datalogger"),
    )


def _arm_version(coordinator: IntelbrasSolarCoordinator) -> str | None:
    """Web UI version, else the firmware family from the Modbus registers."""
    if coordinator.inverter_info and coordinator.inverter_info.arm_version:
        return coordinator.inverter_info.arm_version
    return coordinator.data.arm_firmware if coordinator.data else None


class IntelbrasSolarEntity(CoordinatorEntity[IntelbrasSolarCoordinator]):
    """Common device info and coordinator wiring."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IntelbrasSolarCoordinator,
        entry: ConfigEntry,
        key: str,
        device: str = DEVICE_INVERTER,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        device_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = device_info(coordinator, entry, device)

    @property
    def available(self) -> bool:
        """Unavailable while the inverter sleeps."""
        return super().available and bool(self.coordinator.data.online)
