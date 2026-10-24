"""Config flow for the Intelbras Solar Local integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from intelbras_solar_local import IntelbrasSolarClient, IntelbrasSolarError

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_UNIT,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_UNIT, default=DEFAULT_UNIT): int,
    }
)


class IntelbrasSolarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Intelbras Solar Local config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, Any] = {}

    async def _async_probe(self, host: str, port: int, unit: int):
        """Return the InverterStatus read over Modbus, or None if unreachable."""
        client = IntelbrasSolarClient(
            host, port, unit, session=async_get_clientsession(self.hass)
        )
        try:
            return await client.async_get_inverter_data()
        except IntelbrasSolarError:
            return None
        finally:
            await client.async_close()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            status = await self._async_probe(
                user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_UNIT]
            )
            if status is None:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(status.serial)
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: user_input[CONF_HOST]}
                )
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )

    async def async_step_zeroconf(self, discovery_info) -> ConfigFlowResult:
        """Handle a WiNet-S announcing ``WiNet-WebServer._http._tcp`` (board=WiNet-S).

        The mDNS record only carries the datalogger serial, so the inverter
        serial (the unique id) is read over Modbus. That also moves an existing
        entry to the new IP when DHCP hands the datalogger another address.
        """
        host = discovery_info.host
        self._async_abort_entries_match({CONF_HOST: host})
        status = await self._async_probe(host, DEFAULT_PORT, DEFAULT_UNIT)
        if status is None:
            # Asleep at night or not an inverter: try again on the next announce.
            return self.async_abort(reason="cannot_connect")
        await self.async_set_unique_id(status.serial)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})
        self._discovered = {CONF_HOST: host, "model": status.model or DEFAULT_NAME}
        self.context["title_placeholders"] = {"name": self._discovered["model"]}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_HOST: self._discovered[CONF_HOST],
                    CONF_PORT: DEFAULT_PORT,
                    CONF_UNIT: DEFAULT_UNIT,
                },
            )
        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_NAME, default=DEFAULT_NAME): str}
            ),
            description_placeholders={
                "host": self._discovered[CONF_HOST],
                "model": self._discovered["model"],
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> IntelbrasSolarOptionsFlow:
        return IntelbrasSolarOptionsFlow(config_entry)


class IntelbrasSolarOptionsFlow(OptionsFlow):
    """Handle Intelbras Solar Local options (scan interval)."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self._entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
