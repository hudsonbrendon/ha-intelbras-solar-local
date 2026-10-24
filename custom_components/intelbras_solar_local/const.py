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
