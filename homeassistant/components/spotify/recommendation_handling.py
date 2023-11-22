"""Provides handling for Spotify playlist recommendations in Home Assistant based on weather conditions and dates."""
import logging
from typing import Any, Optional

from spotipy import Spotify, SpotifyException

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .search_string_generator import WeatherPlaylistMapper

_LOGGER = logging.getLogger(__name__)

BROWSE_LIMIT = 48


class RecommendationHandler:
    """A singleton class to handle Spotify playlist recommendations in Home Assistant.

    This class manages recommendations based on weather conditions and dates,
    utilizing the Spotify API to fetch relevant playlists.
    """

    _instance: Optional["RecommendationHandler"] = None

    _last_weather_search_string: str = ""
    _last_api_call_date: str = ""
    _last_api_call_result_weather: list[Any] = []
    _last_api_call_result_date: list[Any] = []

    _media: dict[str, Any] | None = None

    def __new__(cls) -> "RecommendationHandler":
        """Create a new instance of RecommendationHandler or return the existing instance."""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def handling_weather_recommendations(
        self, hass: HomeAssistant, spotify: Spotify
    ) -> tuple[Optional[dict[str, Any]], list]:
        """Fetch Spotify playlists for weather-based recommendations.

        The method uses current weather conditions to generate a search string for querying Spotify
        to find relevant playlists. Caches the last API call result for efficiency.
        """
        current_weather_search_string = self._get_current_weather_search_string(hass)

        if current_weather_search_string is not None:
            return self._fetch_weather_spotify_playlist(
                spotify, current_weather_search_string
            )
        raise HomeAssistantError("Weather data is not available")

    def _get_current_weather_search_string(self, hass: HomeAssistant) -> str | None:
        """Fetch current weather and map it to search string."""

        current_weather_search_string = None

        weather_entity_ids = _get_entity_ids(hass, "weather")
        if not weather_entity_ids:
            raise HomeAssistantError("No weather entity available")
        weather_entity_id = weather_entity_ids[0]
        weather_state = hass.states.get(weather_entity_id)
        try:
            if (
                weather_state is not None
                and "temperature" in weather_state.attributes
                and weather_state.state is not None
            ):
                current_temperature = weather_state.attributes["temperature"]
                condition = weather_state.state
                current_weather_search_string = (
                    WeatherPlaylistMapper().map_weather_to_playlists(
                        current_temperature, condition
                    )
                )
            else:
                raise HomeAssistantError("Weather_state data is not available")
        except ValueError:
            _LOGGER.error(" Search_string value error: {e}")
        return current_weather_search_string

    def _has_weather_changed(self, current_weather_search_string: str) -> bool:
        """Check if the weather state has changed."""
        if self._last_weather_search_string != current_weather_search_string:
            return True
        return False

    def _fetch_weather_spotify_playlist(
        self, spotify: Spotify, current_weather_search_string: str
    ) -> tuple[Optional[dict[str, Any]], list]:
        """Fetch playlist from spotify based on the given search string if the weather state has changed."""
        items = []
        media: dict[str, Any] | None = None
        try:
            if self._has_weather_changed(current_weather_search_string):
                if media := spotify.search(
                    q=current_weather_search_string,
                    type="playlist",
                    limit=BROWSE_LIMIT,
                ):
                    items = media.get("playlists", {}).get("items", [])

                    self._last_api_call_result_weather = items
                    self._last_weather_search_string = current_weather_search_string
                    self._media = media
            else:
                items = self._last_api_call_result_weather
                media = self._media
        except SpotifyException:
            # Handle Spotify API exceptions
            _LOGGER.error("Spotify API error: {e}")
        return media, items


def _get_entity_ids(hass: HomeAssistant, domain: str) -> list[str]:
    """Retrieve entity id's for connected integrations in the given domain."""
    entity_reg = er.async_get(hass)
    return [
        entity.entity_id
        for entity in entity_reg.entities.values()
        if entity.domain == domain
    ]
