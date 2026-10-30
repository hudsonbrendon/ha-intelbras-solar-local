"""Sensors for the Intelbras Solar Local integration."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from intelbras_solar_local import FaultEvent, InverterStatus

from . import IntelbrasSolarConfigEntry
from .const import (
    COAL_KG_PER_KWH,
    DEVICE_DATALOGGER,
    DEVICE_INVERTER,
    DEVICE_PLANT,
    FAULT_TEXT,
    TREES_PER_KG_CO2,
    WORK_STATES,
)
from .coordinator import IntelbrasSolarCoordinator
from .entity import IntelbrasSolarEntity

MEASUREMENT = SensorStateClass.MEASUREMENT
TOTAL_INCREASING = SensorStateClass.TOTAL_INCREASING

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class IntelbrasSolarSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor read from the inverter or the coordinator."""

    value_fn: Callable[[InverterStatus], Any] | None = None
    coordinator_fn: Callable[[IntelbrasSolarCoordinator], Any] | None = None
    attrs_fn: Callable[[IntelbrasSolarCoordinator], dict[str, Any]] | None = None
    device: str = DEVICE_INVERTER
    always_available: bool = False


# Events listed in the fault_events attributes; the full history can be long.
RECENT_FAULTS = 10


def _version(
    c: IntelbrasSolarCoordinator, attr: str, fallback: str | None
) -> str | None:
    """Firmware version from the web UI, else the Modbus family string."""
    return getattr(c.inverter_info, attr, None) or fallback


def _fault_time(event: FaultEvent) -> datetime | None:
    """The inverter logs local wall-clock time; read it in HA's time zone."""
    if event.time is None:
        return None
    return event.time.replace(tzinfo=dt_util.get_default_time_zone())


def _last_fault(c: IntelbrasSolarCoordinator) -> FaultEvent | None:
    """Most recent event that raised a fault (not the one that cleared it)."""
    return next((e for e in c.fault_history or [] if e.active), None)


def _fault_attrs(event: FaultEvent, c: IntelbrasSolarCoordinator) -> dict[str, Any]:
    text = FAULT_TEXT.get(event.name)
    portuguese = c.hass.config.language.startswith("pt")
    return {
        "time": _fault_time(event),
        "fault": event.name,
        "description": (text[1] if portuguese else text[0]) if text else event.name,
        "code": event.code,
        "level": event.level,
        "raised": event.active,
    }


def _round(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)


def _efficiency(status: InverterStatus) -> float | None:
    """AC output over DC input, in %."""
    if not status.power_dc or status.power_ac is None:
        return None
    return round(status.power_ac / status.power_dc * 100, 1)


def _savings(attr: str) -> Callable[[IntelbrasSolarCoordinator], float | None]:
    def _value(c: IntelbrasSolarCoordinator) -> float | None:
        energy = getattr(c.data, attr)
        if c.energy_price <= 0 or energy is None:
            return None
        return round(energy * c.energy_price, 2)

    return _value


def _co2_kg(c: IntelbrasSolarCoordinator) -> float | None:
    if c.data.energy_total is None:
        return None
    return c.data.energy_total * c.co2_factor


def _per_kwp(c: IntelbrasSolarCoordinator, value: float | None) -> float | None:
    capacity = c.capacity_kwp
    if not capacity or value is None:
        return None
    return value / capacity


def _plant_status(c: IntelbrasSolarCoordinator) -> str:
    if not c.data.online:
        return "offline"
    return "fault" if c.data.has_fault else "normal"


def _grid_levels(c: IntelbrasSolarCoordinator) -> int | None:
    """Number of protection levels; ``protection_series`` is 0-based."""
    for param in c.grid_parameters:
        if param.key == "protection_series" and isinstance(param.value, float):
            return int(param.value) + 1
    return None


def _mppt(index: int, attr: str) -> Callable[[InverterStatus], float | None]:
    def _value(status: InverterStatus) -> float | None:
        if len(status.mppts) <= index:
            return None
        return getattr(status.mppts[index], attr)

    return _value


def _power(
    key: str, fn: Callable[[InverterStatus], Any], **kw: Any
) -> IntelbrasSolarSensorEntityDescription:
    return IntelbrasSolarSensorEntityDescription(
        key=key,
        translation_key=key,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=MEASUREMENT,
        value_fn=fn,
        **kw,
    )


def _energy(
    key: str, fn: Callable[[InverterStatus], Any]
) -> IntelbrasSolarSensorEntityDescription:
    return IntelbrasSolarSensorEntityDescription(
        key=key,
        translation_key=key,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=TOTAL_INCREASING,
        value_fn=fn,
    )


def _voltage(
    key: str, fn: Callable[[InverterStatus], Any], **kw: Any
) -> IntelbrasSolarSensorEntityDescription:
    return IntelbrasSolarSensorEntityDescription(
        key=key,
        translation_key=key,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=MEASUREMENT,
        value_fn=fn,
        **kw,
    )


def _current(
    key: str, fn: Callable[[InverterStatus], Any]
) -> IntelbrasSolarSensorEntityDescription:
    return IntelbrasSolarSensorEntityDescription(
        key=key,
        translation_key=key,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=MEASUREMENT,
        value_fn=fn,
    )


SENSORS: tuple[IntelbrasSolarSensorEntityDescription, ...] = (
    _power("ac_power", lambda s: s.power_ac),
    _power("dc_power", lambda s: s.power_dc),
    IntelbrasSolarSensorEntityDescription(
        key="apparent_power",
        translation_key="apparent_power",
        native_unit_of_measurement="VA",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=MEASUREMENT,
        value_fn=lambda s: s.power_apparent,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="reactive_power",
        translation_key="reactive_power",
        native_unit_of_measurement="var",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=MEASUREMENT,
        value_fn=lambda s: s.power_reactive,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="power_factor",
        translation_key="power_factor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=MEASUREMENT,
        value_fn=lambda s: s.power_factor,
    ),
    _energy("energy_today", lambda s: s.energy_today),
    _energy("energy_month", lambda s: s.energy_month),
    _energy("energy_year", lambda s: s.energy_year),
    _energy("energy_total", lambda s: s.energy_total),
    _power("mppt1_power", _mppt(0, "power")),
    _voltage("mppt1_voltage", _mppt(0, "voltage")),
    _current("mppt1_current", _mppt(0, "current")),
    _power("mppt2_power", _mppt(1, "power")),
    _voltage("mppt2_voltage", _mppt(1, "voltage")),
    _current("mppt2_current", _mppt(1, "current")),
    _voltage("grid_voltage", lambda s: s.grid_voltage),
    _current("grid_current", lambda s: s.grid_current),
    IntelbrasSolarSensorEntityDescription(
        key="grid_frequency",
        translation_key="grid_frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=MEASUREMENT,
        value_fn=lambda s: s.grid_frequency,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=MEASUREMENT,
        value_fn=lambda s: s.temperature,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="work_state",
        translation_key="work_state",
        device_class=SensorDeviceClass.ENUM,
        options=[*WORK_STATES.values(), "unknown"],
        value_fn=lambda s: s.work_state,
    ),
    _voltage(
        "bus_voltage",
        lambda s: s.bus_voltage,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="insulation_resistance",
        translation_key="insulation_resistance",
        native_unit_of_measurement="kΩ",
        state_class=MEASUREMENT,
        icon="mdi:omega",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.insulation_resistance,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="fault_code",
        translation_key="fault_code",
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.fault_code,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="active_alarms",
        translation_key="active_alarms",
        icon="mdi:bell-alert-outline",
        state_class=MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.datalogger.total_alarms if s.datalogger else None,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="running_time_today",
        translation_key="running_time_today",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.running_minutes_today,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="running_time_total",
        translation_key="running_time_total",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.running_hours_total,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="nominal_power",
        translation_key="nominal_power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.nominal_power,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="inverter_clock",
        translation_key="inverter_clock",
        icon="mdi:clock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.clock.isoformat(sep=" ") if s.clock else None,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="efficiency",
        translation_key="efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=MEASUREMENT,
        icon="mdi:percent-circle-outline",
        value_fn=_efficiency,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="arm_firmware",
        translation_key="arm_firmware",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=lambda c: _version(c, "arm_version", c.data.arm_firmware),
        attrs_fn=lambda c: {"family": c.data.arm_firmware},
    ),
    IntelbrasSolarSensorEntityDescription(
        key="dsp_firmware",
        translation_key="dsp_firmware",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=lambda c: _version(c, "mdsp_version", c.data.dsp_firmware),
        attrs_fn=lambda c: {
            "family": c.data.dsp_firmware,
            "slave_dsp_version": _version(c, "sdsp_version", None),
            "cpld_version": _version(c, "cpld_version", None),
        },
    ),
    IntelbrasSolarSensorEntityDescription(
        key="fault_events",
        translation_key="fault_events",
        icon="mdi:alert-circle-outline",
        state_class=MEASUREMENT,
        always_available=True,
        coordinator_fn=lambda c: (
            None if c.fault_history is None else sum(e.active for e in c.fault_history)
        ),
        attrs_fn=lambda c: {
            "by_fault": dict(
                Counter(e.name for e in c.fault_history or [] if e.active)
            ),
            "recent": [
                _fault_attrs(e, c) for e in (c.fault_history or [])[:RECENT_FAULTS]
            ],
        },
    ),
    IntelbrasSolarSensorEntityDescription(
        key="last_fault",
        translation_key="last_fault",
        device_class=SensorDeviceClass.TIMESTAMP,
        always_available=True,
        coordinator_fn=lambda c: _last_fault(c) and _fault_time(_last_fault(c)),
        attrs_fn=lambda c: _fault_attrs(_last_fault(c), c) if _last_fault(c) else None,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="rated_reactive_power",
        translation_key="rated_reactive_power",
        native_unit_of_measurement="var",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=lambda c: (
            None
            if c.inverter_info is None or c.inverter_info.rated_reactive_power is None
            else round(c.inverter_info.rated_reactive_power * 1000)
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="grid_protection",
        translation_key="grid_protection",
        icon="mdi:shield-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=_grid_levels,
        attrs_fn=lambda c: {p.key: p.value for p in c.grid_parameters},
    ),
    # Datalogger
    IntelbrasSolarSensorEntityDescription(
        key="wifi_signal",
        translation_key="wifi_signal",
        device=DEVICE_DATALOGGER,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=lambda c: c.wifi_signal.rssi if c.wifi_signal else None,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="wifi_network",
        translation_key="wifi_network",
        device=DEVICE_DATALOGGER,
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=lambda c: c.wifi_signal.ssid if c.wifi_signal else None,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="datalogger_firmware",
        translation_key="datalogger_firmware",
        device=DEVICE_DATALOGGER,
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=lambda c: (
            c.datalogger_info.firmware_version if c.datalogger_info else None
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="datalogger_hardware",
        translation_key="datalogger_hardware",
        device=DEVICE_DATALOGGER,
        icon="mdi:expansion-card-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=lambda c: (
            c.datalogger_info.hardware_version if c.datalogger_info else None
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="cloud_server",
        translation_key="cloud_server",
        device=DEVICE_DATALOGGER,
        icon="mdi:cloud-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=lambda c: (
            c.datalogger_info.cloud_server if c.datalogger_info else None
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="grid_code",
        translation_key="grid_code",
        device=DEVICE_DATALOGGER,
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.DIAGNOSTIC,
        coordinator_fn=lambda c: (
            c.datalogger_info.country if c.datalogger_info else None
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="hotspot_ssid",
        translation_key="hotspot_ssid",
        device=DEVICE_DATALOGGER,
        icon="mdi:access-point",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        coordinator_fn=lambda c: (
            c.datalogger_info.hotspot_ssid if c.datalogger_info else None
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="ntp_server",
        translation_key="ntp_server",
        device=DEVICE_DATALOGGER,
        icon="mdi:clock-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        coordinator_fn=lambda c: (
            c.datalogger_info.ntp_server if c.datalogger_info else None
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="last_record",
        translation_key="last_record",
        device=DEVICE_DATALOGGER,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        always_available=True,
        coordinator_fn=lambda c: c.last_record,
    ),
    # Plant (calculated)
    *(
        IntelbrasSolarSensorEntityDescription(
            key=key,
            translation_key=key,
            device=DEVICE_PLANT,
            native_unit_of_measurement="BRL",
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL if attr == "energy_total" else None,
            coordinator_fn=_savings(attr),
        )
        for key, attr in (
            ("savings_today", "energy_today"),
            ("savings_month", "energy_month"),
            ("savings_year", "energy_year"),
            ("savings_total", "energy_total"),
        )
    ),
    IntelbrasSolarSensorEntityDescription(
        key="co2_avoided",
        translation_key="co2_avoided",
        device=DEVICE_PLANT,
        native_unit_of_measurement="kg",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=TOTAL_INCREASING,
        icon="mdi:molecule-co2",
        coordinator_fn=lambda c: _round(_co2_kg(c), 1),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="trees_saved",
        translation_key="trees_saved",
        device=DEVICE_PLANT,
        state_class=TOTAL_INCREASING,
        icon="mdi:pine-tree",
        coordinator_fn=lambda c: _round(
            None if (co2 := _co2_kg(c)) is None else co2 * TREES_PER_KG_CO2, 2
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="coal_saved",
        translation_key="coal_saved",
        device=DEVICE_PLANT,
        native_unit_of_measurement="kg",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=TOTAL_INCREASING,
        icon="mdi:fire",
        coordinator_fn=lambda c: _round(
            None
            if c.data.energy_total is None
            else c.data.energy_total * COAL_KG_PER_KWH,
            1,
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="specific_yield_today",
        translation_key="specific_yield_today",
        device=DEVICE_PLANT,
        native_unit_of_measurement="kWh/kWp",
        state_class=TOTAL_INCREASING,
        icon="mdi:solar-power-variant-outline",
        coordinator_fn=lambda c: _round(_per_kwp(c, c.data.energy_today), 2),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="utilization",
        translation_key="utilization",
        device=DEVICE_PLANT,
        native_unit_of_measurement=PERCENTAGE,
        state_class=MEASUREMENT,
        icon="mdi:gauge",
        coordinator_fn=lambda c: _round(
            None if (v := _per_kwp(c, c.data.power_ac)) is None else v / 1000 * 100,
            1,
        ),
    ),
    IntelbrasSolarSensorEntityDescription(
        key="installed_capacity",
        translation_key="installed_capacity",
        device=DEVICE_PLANT,
        native_unit_of_measurement="kWp",
        icon="mdi:solar-panel-large",
        coordinator_fn=lambda c: c.capacity_kwp,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="energy_price",
        translation_key="energy_price",
        device=DEVICE_PLANT,
        native_unit_of_measurement="BRL/kWh",
        icon="mdi:cash",
        coordinator_fn=lambda c: c.energy_price or None,
    ),
    IntelbrasSolarSensorEntityDescription(
        key="plant_status",
        translation_key="plant_status",
        device=DEVICE_PLANT,
        device_class=SensorDeviceClass.ENUM,
        options=["normal", "fault", "offline"],
        always_available=True,
        coordinator_fn=_plant_status,
    ),
)

PEAK_POWER = IntelbrasSolarSensorEntityDescription(
    key="peak_power_today",
    translation_key="peak_power_today",
    device=DEVICE_PLANT,
    native_unit_of_measurement=UnitOfPower.WATT,
    device_class=SensorDeviceClass.POWER,
    icon="mdi:chart-bell-curve-cumulative",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IntelbrasSolarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        IntelbrasSolarSensor(coordinator, entry, description) for description in SENSORS
    ]
    entities.append(IntelbrasSolarPeakPower(coordinator, entry, PEAK_POWER))
    async_add_entities(entities)


class IntelbrasSolarSensor(IntelbrasSolarEntity, SensorEntity):
    """A value read from the inverter."""

    entity_description: IntelbrasSolarSensorEntityDescription

    def __init__(
        self,
        coordinator: IntelbrasSolarCoordinator,
        entry: IntelbrasSolarConfigEntry,
        description: IntelbrasSolarSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key, description.device)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if self.entity_description.always_available:
            return self.coordinator.last_update_success
        return super().available

    @property
    def native_value(self) -> Any:
        description = self.entity_description
        if description.coordinator_fn is not None:
            return description.coordinator_fn(self.coordinator)
        return description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator)


class IntelbrasSolarPeakPower(IntelbrasSolarEntity, RestoreSensor):
    """Highest AC power seen today; restored across restarts on the same day."""

    entity_description: IntelbrasSolarSensorEntityDescription

    def __init__(
        self,
        coordinator: IntelbrasSolarCoordinator,
        entry: IntelbrasSolarConfigEntry,
        description: IntelbrasSolarSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, entry, description.key, description.device)
        self.entity_description = description
        self._peak: int | None = None
        self._day: datetime | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_sensor_data()
        state = await self.async_get_last_state()
        if last is not None and state is not None:
            changed = dt_util.as_local(state.last_changed).date()
            if changed == dt_util.now().date() and last.native_value is not None:
                self._peak = int(float(last.native_value))
                self._day = dt_util.now()
        self._update_peak()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_peak()
        super()._handle_coordinator_update()

    def _update_peak(self) -> None:
        today = dt_util.now()
        if self._day is None or self._day.date() != today.date():
            self._peak, self._day = None, today
        power = self.coordinator.data.power_ac if self.coordinator.data else None
        if power is not None and (self._peak is None or power > self._peak):
            self._peak = power

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> int | None:
        return self._peak
