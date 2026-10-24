"""DataUpdateCoordinator for the Intelbras Solar Local integration."""
from __future__ import annotations

import logging
import time
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


# A poll that starts within this window after a write may still read the old
# register value (the WiNet-S lags about a second), so written fields win.
WRITE_SETTLE_SECONDS = 3
# Consecutive failed polls before the inverter is reported offline. Single
# timeouts happen (Wi-Fi hiccups, another Modbus client) and must not flap
# every entity to unavailable.
OFFLINE_AFTER_FAILURES = 3


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
        self._failures = 0
        self._written: dict[str, Any] = {}
        self._written_at = 0.0

    async def _async_update_data(self) -> InverterStatus:
        """Fetch status; an asleep inverter is not a fatal error.

        The inverter powers down at night and takes the datalogger's Modbus
        with it, so repeated failures become ``online=False`` instead of an
        UpdateFailed that would spam the log every poll until sunrise.
        """
        started = time.monotonic()
        try:
            status = await self.client.async_get_status()
        except IntelbrasSolarError as err:
            self._failures += 1
            _LOGGER.debug("Inverter read failed (%s in a row): %s", self._failures, err)
            if self.data is not None and self.data.online:
                if self._failures < OFFLINE_AFTER_FAILURES:
                    return self.data
            return InverterStatus(online=False)
        self._failures = 0
        if self._written:
            if started - self._written_at < WRITE_SETTLE_SECONDS:
                return replace(status, **self._written)
            self._written = {}
        return status

    def async_set_written(self, **fields: Any) -> None:
        """Show a successful write right away.

        The WiNet-S takes about a second to reflect a holding-register write, and
        a poll already in flight would otherwise bring the old value back.
        """
        self._written |= fields
        self._written_at = time.monotonic()
        self.async_set_updated_data(replace(self.data, **fields))
