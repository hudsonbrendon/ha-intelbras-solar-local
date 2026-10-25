"""Constants for the Intelbras Solar Local integration."""
from __future__ import annotations

# Re-export protocol constants from the library so platform modules can keep
# their `from .const import ...` imports in one place.
from intelbras_solar_local import (  # noqa: F401
    DEFAULT_PORT,
    DEFAULT_UNIT,
    WORK_STATES,
)

DOMAIN = "intelbras_solar_local"

DEFAULT_NAME = "Intelbras Solar Local"
MANUFACTURER = "Intelbras (Sungrow)"

CONF_UNIT = "unit"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 15
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 600

# Plant options (calculated sensors)
CONF_ENERGY_PRICE = "energy_price"  # BRL per kWh; 0 disables the savings sensors
CONF_INSTALLED_CAPACITY = "installed_capacity"  # kWp; 0 uses the inverter rating
CONF_CO2_FACTOR = "co2_factor"  # kg CO2 avoided per kWh
DEFAULT_ENERGY_PRICE = 0.0
DEFAULT_INSTALLED_CAPACITY = 0.0
# Same factors as the Intelbras Solar Plus app, so both report the same numbers.
DEFAULT_CO2_FACTOR = 0.3406
COAL_KG_PER_KWH = 0.4
# The app's "trees saved" equals tonnes of CO2 avoided.
TREES_PER_KG_CO2 = 0.001

# Device kinds an entity can belong to
DEVICE_INVERTER = "inverter"
DEVICE_DATALOGGER = "datalogger"
DEVICE_PLANT = "plant"
