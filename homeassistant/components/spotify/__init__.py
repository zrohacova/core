"""The spotify integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any, Final

import aiohttp
import requests
from spotipy import Spotify, SpotifyException
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .browse_media import async_browse_media
from .const import DOMAIN, LOGGER, SPOTIFY_SCOPES
from .date_search_string import HolidayDateMapper
from .util import (
    is_spotify_media_type,
    resolve_spotify_media_type,
    spotify_uri_from_media_browser_url,
)

PLATFORMS = [Platform.MEDIA_PLAYER]
SERVICE_SET_TIMEFRAME: Final = "set_timeframe"

# Schema for set timeframe
SET_TIMEFRAME_SCHEMA = vol.Schema(
    {
        vol.Required("timeframe"): vol.Coerce(int),
        vol.Required("time_unit"): vol.Coerce(str),
    }
)

_LOGGER = logging.getLogger(__name__)

__all__ = [
    "async_browse_media",
    "DOMAIN",
    "spotify_uri_from_media_browser_url",
    "is_spotify_media_type",
    "resolve_spotify_media_type",
]


@dataclass
class HomeAssistantSpotifyData:
    """Spotify data stored in the Home Assistant data object."""

    client: Spotify
    current_user: dict[str, Any]
    devices: DataUpdateCoordinator[list[dict[str, Any]]]
    session: OAuth2Session


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spotify from a config entry."""
    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)

    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    spotify = Spotify(auth=session.token["access_token"])

    try:
        current_user = await hass.async_add_executor_job(spotify.me)
    except SpotifyException as err:
        raise ConfigEntryNotReady from err

    if not current_user:
        raise ConfigEntryNotReady

    async def _update_devices() -> list[dict[str, Any]]:
        if not session.valid_token:
            await session.async_ensure_token_valid()
            await hass.async_add_executor_job(
                spotify.set_auth, session.token["access_token"]
            )

        try:
            devices: dict[str, Any] | None = await hass.async_add_executor_job(
                spotify.devices
            )
        except (requests.RequestException, SpotifyException) as err:
            raise UpdateFailed from err

        if devices is None:
            return []

        return devices.get("devices", [])

    device_coordinator: DataUpdateCoordinator[
        list[dict[str, Any]]
    ] = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=f"{entry.title} Devices",
        update_interval=timedelta(minutes=5),
        update_method=_update_devices,
    )
    await device_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = HomeAssistantSpotifyData(
        client=spotify,
        current_user=current_user,
        devices=device_coordinator,
        session=session,
    )

    async def handle_set_timeframe(call: ServiceCall):
        """Handle the set_timeframe service call."""
        timeframe = call.data.get("timeframe")
        time_unit = call.data.get("time_unit")

        # Ensure timeframe is an integer
        if timeframe is None:
            _LOGGER.error("Timeframe is not provided or invalid")
            return

        # Convert weeks and months to days if needed
        timeframe, time_unit = convert_timeframe(timeframe, time_unit)

        update_timeframe_in_hass_data(timeframe)

        # Update time unit in hass data
        hass.data[DOMAIN]["time_unit"] = time_unit

        # Update the HolidayDateMapper instance in hass.data
        update_holiday_mapper(hass)

    def convert_timeframe(timeframe, time_unit):
        """Convert weeks and months to days if needed."""
        if time_unit == "weeks":
            timeframe *= 7
        elif time_unit == "months":
            timeframe *= 30

        return timeframe, "days"

    def update_timeframe_in_hass_data(timeframe):
        """Update timeframe values in hass.data."""
        if timeframe != hass.data[DOMAIN].get("timeframe"):
            hass.data[DOMAIN]["timeframe_updated"] = "TRUE"

        hass.data[DOMAIN]["timeframe"] = timeframe

    def update_holiday_mapper(hass: HomeAssistant):
        """Update the HolidayDateMapper instance in hass.data."""
        holiday_mapper = hass.data[DOMAIN]["holiday_mapper"]
        holiday_mapper.update_values()

    # Create an instance of HolidayDateMapper with hass instance
    hass.data[DOMAIN]["holiday_mapper"] = HolidayDateMapper(hass)

    # Register the service set timeframe
    hass.services.async_register(
        DOMAIN, SERVICE_SET_TIMEFRAME, handle_set_timeframe, schema=SET_TIMEFRAME_SCHEMA
    )

    if not set(session.token["scope"].split(" ")).issuperset(SPOTIFY_SCOPES):
        raise ConfigEntryAuthFailed

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Spotify config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        del hass.data[DOMAIN][entry.entry_id]
    return unload_ok
