"""Base entity for the Intelbras Solar Local integration."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from intelbras_solar_local import IntelbrasSolarError, Parameter

from .const import (
    DEVICE_DATALOGGER,
    DEVICE_INVERTER,
    DEVICE_PLANT,
    DOMAIN,
    MANUFACTURER,
    PARAMETER_ACTION_ONLY,
    PARAMETERS,
)
from .coordinator import IntelbrasSolarCoordinator


def device_info(
    coordinator: IntelbrasSolarCoordinator, entry: ConfigEntry, kind: str
) -> DeviceInfo:
    """Inverter, datalogger and plant devices, like the Intelbras cloud splits them.

    The inverter keeps the serial-only identifier it had before the split, so
    existing entities stay on it. It is not linked to the datalogger:
    ``via_device`` is deprecated and ``via_device_id`` is missing before 2025.
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


def parameter_platform(param: Parameter) -> str:
    """Entity platform for a parameter: switch, select or number."""
    if set(param.options) == {"enable", "prohibited"}:
        return "switch"
    return "select" if param.options else "number"


def async_add_parameter_entities(
    coordinator: IntelbrasSolarCoordinator,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    platform: str,
    factory: Callable[[IntelbrasSolarCoordinator, ConfigEntry, Parameter], Entity],
) -> None:
    """Add parameter entities as their parameters show up.

    Parameters are read in the background (and not at all while the inverter
    sleeps), so the entities can only be created once a read succeeds.
    """
    known: set[tuple[int, int | None]] = set()

    @callback
    def _add_new() -> None:
        new = []
        for param in coordinator.parameters:
            ident = (param.kind, param.register)
            if (
                ident in known
                or param.key in PARAMETER_ACTION_ONLY
                or parameter_platform(param) != platform
            ):
                continue
            known.add(ident)
            new.append(factory(coordinator, entry, param))
        if new:
            async_add_entities(new)

    _add_new()
    entry.async_on_unload(coordinator.async_add_listener(_add_new))


class IntelbrasSolarParameterEntity(IntelbrasSolarEntity):
    """An inverter parameter from the web UI, written through the datalogger."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: IntelbrasSolarCoordinator,
        entry: ConfigEntry,
        param: Parameter,
    ) -> None:
        super().__init__(coordinator, entry, f"param_{param.kind}_{param.register}")
        self._kind = param.kind
        self._key = param.key
        translation, enabled = PARAMETERS.get(param.key, (None, False))
        if translation:
            self._attr_translation_key = translation
        else:
            # A parameter of another model: no translation, plain name.
            self._attr_name = param.key.replace("_", " ").capitalize()
        self._attr_entity_registry_enabled_default = enabled

    @property
    def parameter(self) -> Parameter | None:
        """The parameter as last read."""
        return next(
            (
                p
                for p in self.coordinator.parameters
                if p.kind == self._kind and p.key == self._key
            ),
            None,
        )

    @property
    def available(self) -> bool:
        return super().available and self.parameter is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        param = self.parameter
        if param is None:
            return None
        attrs: dict[str, Any] = {"register": param.register}
        if param.levels is not None:
            level = next(
                (p.value for p in self.coordinator.parameters
                 if p.key == "protection_series"),
                None,
            )
            # Settings of protection levels above the active one are ignored.
            attrs["applies"] = level is None or int(float(level)) in param.levels
        return attrs

    async def _async_write(self, value: float | str) -> None:
        param = self.parameter
        if param is None:
            raise HomeAssistantError("Parameter not read from the inverter yet")
        try:
            await self.coordinator.async_set_parameter(param, value)
        except (IntelbrasSolarError, ValueError) as err:
            raise HomeAssistantError(f"Failed to set {param.key}: {err}") from err
