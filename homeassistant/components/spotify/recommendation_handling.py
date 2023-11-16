"""Provides handling for Spotify playlist recommendations in Home Assistant based on weather conditions and dates."""
import logging
from typing import Any, Optional

from spotipy import Spotify, SpotifyException

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

BROWSE_LIMIT = 48

_LOGGER = logging.getLogger(__name__)


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

    def __new__(cls) -> "RecommendationHandler":  # singleton pattern
        """Create a new instance of RecommendationHandler or return the existing instance."""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def handling_weather_recommendations(self, hass: HomeAssistant, spotify: Spotify):
        """Fetch Spotify playlists for weather-based recommendations.

        The method uses current weather conditions to generate a search string for querying Spotify
        to find relevant playlists. Caches the last API call result for efficiency.
        """
        items = []
        media: dict[str, Any] | None = None

        current_weather_search_string = "cold rain"

        try:
            if self._last_weather_search_string != current_weather_search_string:
                if media := spotify.search(
                    q=current_weather_search_string, type="playlist", limit=BROWSE_LIMIT
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
            _LOGGER.info("Spotify API error: {e}")
            media = None

        return media, items

    def handling_date_recommendations(self, hass: HomeAssistant, spotify: Spotify):
        """Fetch Spotify playlists for date-based recommendations using a predefined query."""
        items = []
        media: dict[str, Any] | None = None

        # Define the search query for current date
        current_date_search_string = "winter"  # FIX: This should be dynamically determined based on the current date
        current_date = dt_util.now().date().isoformat()

        # Check if the last API call date is valid and different from the current date
        if (
            not self._is_valid_date(self._last_api_call_date)
            or self._last_api_call_date != current_date
        ):
            try:
                if media := spotify.search(
                    q=current_date_search_string, type="playlist", limit=BROWSE_LIMIT
                ):
                    items = media.get("playlists", {}).get("items", [])

                    self._last_api_call_result_date = items
                    self._last_api_call_date = current_date
                    self._media = media
            except SpotifyException:
                # Handle Spotify API exceptions
                _LOGGER.info("Spotify API error: {e}")
        else:
            # Use cached results if the date hasn't changed and the last call date is valid
            items = self._last_api_call_result_date
            media = self._media
        return media, items

    def _is_valid_date(self, date_str: str) -> bool:
        """Check if a date string is in a valid format."""
        parsed_date = dt_util.parse_date(date_str)
        if parsed_date is None:
            # Date parsing failed, invalid format
            _LOGGER.warning("Invalid Date Format: %s", date_str)
            return False
        return True
