from spotipy import Spotify  # noqa: D100
from typing import Any
from homeassistant.core import HomeAssistant

BROWSE_LIMIT = 48

class RecommendationHandling:  # noqa: D101

    _instance = None

    _last_weather_search_string = ""
    _last_api_call_result_weather = []

    def __new__(cls): # singleton pattern
        if not cls._instance:
            cls._instance = super(RecommendationHandling, cls).__new__(cls)
        return cls._instance

    def handling_weather_recommendatios(  # noqa: D102
        self, hass: HomeAssistant, spotify: Spotify
    ):  # noqa: D102

        items = []
        media: dict[str, Any] | None = None

        '''weather_entity_id = "weather.home"
        weather_state = hass.states.get(weather_entity_id)

        if (
            weather_state is not None
            and "temperature" in weather_state.attributes
            and "forecast" in weather_state.attributes
        ):
            current_temperature = weather_state.attributes["temperature"]  # noqa: F841
            condition = weather_state.attributes["forecast"][0][  # noqa: F841
                "condition"
            ]  # noqa: F841
            # send current_temperature and condition to search_string_generator and get search string
           '''
        current_weather_search_string = "cold rain"

        if self._last_weather_search_string != current_weather_search_string:
            if media := spotify.search(q=current_weather_search_string, type="playlist", limit=BROWSE_LIMIT):
                items = media.get("playlists", {}).get("items", [])

                self._last_api_call_result_weather = items
                self._last_weather_search_string = current_weather_search_string
        else:
            items = self._last_api_call_result_weather

        return media, items
