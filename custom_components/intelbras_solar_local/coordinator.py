"""DataUpdateCoordinator for the Intelbras Solar Local integration."""
from __future__ import annotations

import logging
import time
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from intelbras_solar_local import (
    DataloggerInfo,
    FaultEvent,
    GridParameter,
    IntelbrasSolarClient,
    IntelbrasSolarError,
    InverterInfo,
    InverterStatus,
    WifiSignal,
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
# Datalogger/inverter identity, Wi-Fi signal (a ~3 s station scan), grid
# settings and the fault history barely move; they refresh on this slower
# cadence instead of every poll.
SLOW_EXTRAS_INTERVAL = timedelta(minutes=10)


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
        self.datalogger_info: DataloggerInfo | None = None
        self.wifi_signal: WifiSignal | None = None
        self.grid_parameters: list[GridParameter] = []
        self.inverter_info: InverterInfo | None = None
        self.fault_history: list[FaultEvent] = []
        self.last_record: datetime | None = None
        # Plant settings, filled from the options in async_setup_entry.
        self.energy_price = 0.0
        self.installed_capacity = 0.0
        self.co2_factor = 0.0
        self._failures = 0
        self._written: dict[str, Any] = {}
        self._written_at = 0.0
        self._slow_extras_at: datetime | None = None

    @property
    def capacity_kwp(self) -> float | None:
        """Installed capacity: the option, else the inverter's nominal power."""
        if self.installed_capacity > 0:
            return self.installed_capacity
        return self.data.nominal_power if self.data else None

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
        self.last_record = dt_util.utcnow()
        await self._async_refresh_slow_extras()
        if self._written:
            if started - self._written_at < WRITE_SETTLE_SECONDS:
                return replace(status, **self._written)
            self._written = {}
        return status

    async def _async_refresh_slow_extras(self) -> None:
        """Best-effort refresh of the slow datalogger extras; never raises."""
        now = dt_util.utcnow()
        if self._slow_extras_at and now - self._slow_extras_at < SLOW_EXTRAS_INTERVAL:
            return
        self._slow_extras_at = now
        self.datalogger_info = await self._safe(
            self.client.async_get_datalogger_info(), self.datalogger_info
        )
        self.wifi_signal = await self._safe(
            self.client.async_get_wifi_signal(), self.wifi_signal
        )
        self.grid_parameters = await self._safe(
            self.client.async_get_grid_parameters(), self.grid_parameters
        )
        self.inverter_info = await self._safe(
            self.client.async_get_inverter_info(), self.inverter_info
        )
        self.fault_history = await self._safe(
            self.client.async_get_fault_history(), self.fault_history
        )

    async def _safe(self, coro, default):
        """Await coro, keeping the previous value on a datalogger error."""
        try:
            return await coro
        except IntelbrasSolarError as err:
            _LOGGER.debug("Datalogger extra fetch failed: %s", err)
            return default

    def async_set_written(self, **fields: Any) -> None:
        """Show a successful write right away.

        The WiNet-S takes about a second to reflect a holding-register write, and
        a poll already in flight would otherwise bring the old value back.
        """
        self._written |= fields
        self._written_at = time.monotonic()
        self.async_set_updated_data(replace(self.data, **fields))
