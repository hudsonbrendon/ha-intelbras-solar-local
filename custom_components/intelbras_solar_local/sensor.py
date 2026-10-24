"""Sensors for the Intelbras Solar Local integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from intelbras_solar_local import InverterStatus

from .const import DOMAIN, WORK_STATES
from .entity import IntelbrasSolarEntity

MEASUREMENT = SensorStateClass.MEASUREMENT
TOTAL_INCREASING = SensorStateClass.TOTAL_INCREASING


@dataclass(frozen=True, kw_only=True)
class IntelbrasSolarSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[InverterStatus], str | int | float | None]


def _mppt(index: int, attr: str) -> Callable[[InverterStatus], float | None]:
    def _value(status: InverterStatus) -> float | None:
        if len(status.mppts) <= index:
            return None
        return getattr(status.mppts[index], attr)

    return _value


def _power(key, fn, **kw) -> IntelbrasSolarSensorEntityDescription:
    return IntelbrasSolarSensorEntityDescription(
        key=key,
        translation_key=key,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=MEASUREMENT,
        value_fn=fn,
        **kw,
    )


def _energy(key, fn) -> IntelbrasSolarSensorEntityDescription:
    return IntelbrasSolarSensorEntityDescription(
        key=key,
        translation_key=key,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=TOTAL_INCREASING,
        value_fn=fn,
    )


def _voltage(key, fn, **kw) -> IntelbrasSolarSensorEntityDescription:
    return IntelbrasSolarSensorEntityDescription(
        key=key,
        translation_key=key,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=MEASUREMENT,
        value_fn=fn,
        **kw,
    )


def _current(key, fn) -> IntelbrasSolarSensorEntityDescription:
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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        IntelbrasSolarSensor(coordinator, entry, description) for description in SENSORS
    )


class IntelbrasSolarSensor(IntelbrasSolarEntity, SensorEntity):
    """A value read from the inverter."""

    entity_description: IntelbrasSolarSensorEntityDescription

    def __init__(self, coordinator, entry, description) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> str | int | float | None:
        return self.entity_description.value_fn(self.coordinator.data)
