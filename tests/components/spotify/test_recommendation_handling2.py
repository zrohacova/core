"""Test Spotify Recommendation Handler."""

from unittest.mock import patch

from homeassistant.components.spotify.recommendation_handling import (
    RecommendationHandler,
)
from homeassistant.core import HomeAssistant

from tests.components.accuweather import init_integration


async def test_handling_weather_recommendations(hass: HomeAssistant) -> None:
    """Test handling weather recommendations."""
    handler = RecommendationHandler()
    await init_integration(hass)

    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {
                "items": [
                    {"name": "Sunny Day Playlist 1", "id": "playlist_id_1"},
                    {"name": "Sunny Day Playlist 2", "id": "playlist_id_2"},
                ]
            }
        }

        media, items = handler.handling_weather_recommendations(hass, spotify_mock)

        assert items
        assert media

        assert len(items) == 2
