"""Provides handling for Spotify playlist recommendations in Home Assistant based on weather conditions and dates."""
import logging
from typing import Any, Optional

from spotipy import Spotify, SpotifyException

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .date_search_string import HolidayDateMapper
from .weather_search_string import WeatherPlaylistMapper

# Limit the number of items fetched from Spotify
BROWSE_LIMIT = 48

_LOGGER = logging.getLogger(__name__)


class RecommendationHandler:
    """A singleton class to handle Spotify playlist recommendations in Home Assistant.

    This class manages recommendations based on weather conditions and dates,
    utilizing the Spotify API to fetch relevant playlists.
    """

    _instance: Optional["RecommendationHandler"] = None

    # Variables for caching API call results and search strings
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
        holiday_date_mapper = HolidayDateMapper(hass)
        weather_entity_ids = holiday_date_mapper.get_entity_ids(hass, "weather")
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

    def handling_date_recommendations(
        self, spotify: Spotify, hass: HomeAssistant, user: Any
    ) -> tuple[Optional[dict[str, Any]], list]:
        """Fetch Spotify playlists for date-based recommendations."""
        try:
            # Generate a search string based on the current date
            current_date_search_string = self._generate_date_search_string(hass, user)
            current_date = dt_util.now().date().isoformat()

            # Fetch playlists if the date has changed since the last API call or issue with previous API call
            if self._is_new_date(hass, current_date):
                return self._fetch_spotify_playlists(
                    spotify, current_date_search_string, current_date
                )
            return self._media, self._last_api_call_result_date

        except HomeAssistantError as e:
            _LOGGER.error("Home Assistant error: %s", e)
            raise
        except SpotifyException as e:
            _LOGGER.error("Spotify API error: %s", e)
            # Inform the user about the API issue
            raise HomeAssistantError(
                "There was an issue connecting to Spotify. Please try again later."
            ) from e
        except ValueError as e:
            _LOGGER.error("Value error encountered: %s", e)

        return None, []

    def _generate_date_search_string(self, hass: HomeAssistant, user: Any) -> str:
        """Generate a search string based on the current date."""
        # Implement logic to dynamically generate the search string based on the current date
        search_string = self.determine_search_string_based_on_date(hass, user)

        if search_string is None:
            raise HomeAssistantError(
                "Oops! It looks like you haven't set up a calendar integration yet. "
                "Please connect a calendar integration in the settings."
            )

        return search_string

    def _is_new_date(self, hass: HomeAssistant, current_date: str) -> bool:
        """Check if the current date is different from the last API call date or issue with previous API call."""
        return (
            dt_util.parse_date(self._last_api_call_date) is None
            or self._last_api_call_date != current_date
            or hass.data[DOMAIN].get("timeframe_updated") == "TRUE"
        )

    def _fetch_spotify_playlists(
        self, spotify: Spotify, search_string: str, current_date: str
    ) -> tuple[Optional[dict[str, Any]], list]:
        """Fetch playlists from Spotify based on the given search string."""
        media = spotify.search(q=search_string, type="playlist", limit=BROWSE_LIMIT)
        items = media.get("playlists", {}).get("items", [])

        # Limit the number of items to BROWSE_LIMIT
        if len(items) > BROWSE_LIMIT:
            items = items[:BROWSE_LIMIT]

        if not items:
            _LOGGER.error(
                "No playlists found for the given search string: %s", search_string
            )
            raise HomeAssistantError(
                "There was an issue with fetching the playlists from spotify for current date. Please check back later."
            )

        # Update cache with the latest API call results
        self._last_api_call_result_date = items
        self._last_api_call_date = current_date
        self._media = media

        return media, items

    def determine_search_string_based_on_date(
        self, hass: HomeAssistant, user: Any
    ) -> Optional[str]:
        """Determine the search string for Spotify playlists based on the current date."""
        holiday_date_mapper = HolidayDateMapper(hass)
        search_string = holiday_date_mapper.search_string_date(hass, user)
        return search_string
