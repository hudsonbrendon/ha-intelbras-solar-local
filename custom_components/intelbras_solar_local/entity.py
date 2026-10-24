"""Base entity for the Intelbras Solar Local integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import IntelbrasSolarCoordinator


class IntelbrasSolarEntity(CoordinatorEntity[IntelbrasSolarCoordinator]):
    """Common device info and coordinator wiring."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IntelbrasSolarCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        device_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{device_id}_{key}"
        data = coordinator.data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=data.model if data else None,
            serial_number=entry.unique_id,
            configuration_url=f"http://{coordinator.client.host}",
        )

    @property
    def available(self) -> bool:
        """Unavailable while the inverter sleeps."""
        return super().available and bool(self.coordinator.data.online)
