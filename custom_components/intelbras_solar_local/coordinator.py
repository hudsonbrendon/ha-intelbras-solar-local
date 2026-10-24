"""DataUpdateCoordinator for the Intelbras Solar Local integration."""
from __future__ import annotations

import logging
from dataclasses import replace
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from intelbras_solar_local import (
    IntelbrasSolarClient,
    IntelbrasSolarError,
    InverterStatus,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IntelbrasSolarCoordinator(DataUpdateCoordinator[InverterStatus]):
    """Polls the inverter and exposes an InverterStatus to entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: IntelbrasSolarClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> InverterStatus:
        """Fetch status; an asleep inverter is not a fatal error.

        The inverter powers down at night and takes the datalogger's Modbus
        with it, so a failed read becomes ``online=False`` instead of an
        UpdateFailed that would spam the log every poll until sunrise.
        """
        try:
            return await self.client.async_get_status()
        except IntelbrasSolarError as err:
            _LOGGER.debug("Inverter unreachable: %s", err)
            return InverterStatus(online=False)

    def async_set_written(self, **fields: Any) -> None:
        """Show a successful write right away.

        The WiNet-S takes about a second to reflect a holding-register write, so
        an immediate refresh reads the old value (and the debouncer then holds
        further refreshes). The next scheduled poll confirms the new value.
        """
        self.async_set_updated_data(replace(self.data, **fields))
