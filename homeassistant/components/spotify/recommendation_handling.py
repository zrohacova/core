"""Provides handling for Spotify playlist recommendations in Home Assistant based on weather conditions and dates."""
import logging
from typing import Any, Optional

from spotipy import Spotify, SpotifyException

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .search_string_generator import WeatherPlaylistMapper

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
        current_weather_search_string = None

        weather_entity_id = "weather.home"
        weather_state = hass.states.get(weather_entity_id)
        try:
            if (
                weather_state is not None
                and "temperature" in weather_state.attributes
                and "forecast" in weather_state.attributes
            ):
                current_temperature = weather_state.attributes["temperature"]
                condition = weather_state.attributes["forecast"][0]["condition"]
                current_weather_search_string = (
                    WeatherPlaylistMapper().map_weather_to_playlists(
                        current_temperature, condition
                    )
                )
            else:
                raise HomeAssistantError("Weather_state data is not available")

        except ValueError:
            _LOGGER.error(" Search_string value error: {e}")

        if current_weather_search_string is not None:
            try:
                if self._last_weather_search_string != current_weather_search_string:
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
        else:
            raise HomeAssistantError(
                "Oops! It looks like you haven't set up a weather integration yet. Please connect a weather integration in the settings."
            )
        return media, items

    def handling_date_recommendations(
        self, hass: HomeAssistant, spotify: Spotify
    ) -> tuple[Optional[dict[str, Any]], list]:
        """Fetch Spotify playlists for date-based recommendations."""
        try:
            current_date_search_string = self._generate_date_search_string()
            current_date = dt_util.now().date().isoformat()

            if self._is_new_date(current_date):
                return self._fetch_spotify_playlists(
                    spotify, current_date_search_string, current_date
                )
            return self._media, self._last_api_call_result_date

        except HomeAssistantError as e:
            _LOGGER.error("Home Assistant error: %s", e)
            raise
        except SpotifyException as e:
            _LOGGER.error("Spotify API error: %s", e)
            raise

    def _generate_date_search_string(self) -> str:
        # Implement logic to dynamically generate the search string based on the current date
        search_string = "winter"

        if search_string is None:
            raise HomeAssistantError(
                "Oops! It looks like you haven't set up a calendar integration yet. "
                "Please connect a calendar integration in the settings."
            )

        return search_string

    def _is_new_date(self, current_date: str) -> bool:
        return (
            dt_util.parse_date(self._last_api_call_date) is None
            or self._last_api_call_date != current_date
        )

    def _fetch_spotify_playlists(
        self, spotify: Spotify, search_string: str, current_date: str
    ) -> tuple[Optional[dict[str, Any]], list]:
        media = spotify.search(q=search_string, type="playlist", limit=BROWSE_LIMIT)
        items = media.get("playlists", {}).get("items", [])

        self._last_api_call_result_date = items
        self._last_api_call_date = current_date
        self._media = media

        return media, items
