"""Actions for the Intelbras Solar Local integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from intelbras_solar_local import IntelbrasSolarError

from .const import DOMAIN
from .coordinator import IntelbrasSolarCoordinator

SERVICE_SET_PARAMETER = "set_parameter"
SET_PARAMETER_SCHEMA = vol.Schema(
    {
        # Library key (e.g. "standby_time") or register (e.g. "30091").
        vol.Required("parameter"): cv.string,
        vol.Required("value"): vol.Any(vol.Coerce(float), cv.string),
    }
)


async def _set_parameter(call: ServiceCall) -> None:
    wanted = call.data["parameter"]
    for entry in call.hass.config_entries.async_loaded_entries(DOMAIN):
        coordinator: IntelbrasSolarCoordinator = entry.runtime_data
        for param in coordinator.parameters:
            if wanted in (param.key, str(param.register)):
                value = call.data["value"]
                if param.options:
                    value = str(value)
                try:
                    await coordinator.async_set_parameter(param, value)
                except ValueError as err:
                    raise ServiceValidationError(str(err)) from err
                except IntelbrasSolarError as err:
                    raise HomeAssistantError(
                        f"Failed to set {param.key}: {err}"
                    ) from err
                return
    raise ServiceValidationError(
        f"Unknown parameter {wanted!r}; the inverter parameters are read a few "
        "seconds after start-up and only while the inverter is on"
    )


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the set_parameter action."""
    hass.services.async_register(
        DOMAIN, SERVICE_SET_PARAMETER, _set_parameter, schema=SET_PARAMETER_SCHEMA
    )
