"""Diagnostics support for the Intelbras Solar Local integration."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import IntelbrasSolarCoordinator

TO_REDACT = {"serial"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: IntelbrasSolarCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data
    return {
        "entry": {
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "status": async_redact_data(asdict(data), TO_REDACT) if data else None,
        "derived": {
            "model": data.model,
            "work_state": data.work_state,
            "producing": data.producing,
            "has_fault": data.has_fault,
        }
        if data
        else None,
    }
