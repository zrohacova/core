"""Config flow for the Thread integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components import onboarding, zeroconf
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class ThreadConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Thread."""

    VERSION = 1

    async def async_step_import(
        self, import_data: dict[str, str] | None = None
    ) -> FlowResult:
        """Set up by import from async_setup."""
        await self._async_handle_discovery_without_unique_id()
        return self.async_create_entry(title="Thread", data={})

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Set up by import from async_setup."""
        await self._async_handle_discovery_without_unique_id()
        return self.async_create_entry(title="Thread", data={})

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Set up because the user has border routers."""
        await self._async_handle_discovery_without_unique_id()
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the setup."""
        if user_input is not None or not onboarding.async_is_onboarded(self.hass):
            return self.async_create_entry(title="Thread", data={})
        return self.async_show_form(step_id="confirm")

    # async def async_import(self, data: dict[str, str] | None = None) -> FlowResult:
    #    """Set up by import from async_setup.
    #    Data represents either input from user or imported data, which should be given in the call of the method.
    #    """
    #    await self._async_handle_discovery_without_unique_id()
    #    return self.async_create_entry(title="Thread", data={})
