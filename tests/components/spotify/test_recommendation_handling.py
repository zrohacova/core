"""Test Spotify Recommendation Handler."""

from unittest.mock import patch

from homeassistant.components.spotify.recommendation_handling import (
    RecommendationHandler,
)
from homeassistant.core import HomeAssistant


async def test_handling_weather_recommendations(hass: HomeAssistant) -> None:
    """Test handling weather recommendations."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Cold Rain Playlist"}]}
        }

        handler = RecommendationHandler()
        media, items = handler.handling_weather_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert len(items) == 1
        assert items[0]["name"] == "Cold Rain Playlist"
        assert media is not None


async def test_handling_weather_recommendations_empty_playlist(
    hass: HomeAssistant,
) -> None:
    """Test handling weather recommendations with an empty playlist response."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {"playlists": {"items": []}}

        handler = RecommendationHandler()
        # Reset the last search string to ensure the search method is called
        handler._last_weather_search_string = ""
        media, items = handler.handling_weather_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert items == []
        assert media is not None


async def test_handling_weather_recommendations_caching(hass: HomeAssistant) -> None:
    """Test caching mechanism in weather recommendations."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Cold Rain Playlist"}]}
        }

        handler = RecommendationHandler()

        # First call
        handler.handling_weather_recommendations(hass, spotify_mock)
        assert spotify_mock.search.called_once

        # Reset mock call count
        spotify_mock.search.reset_mock()

        # Second call with the same parameters
        handler.handling_weather_recommendations(hass, spotify_mock)
        assert not spotify_mock.search.called


async def test_handling_different_weather_conditions(hass: HomeAssistant) -> None:
    """Test handling different weather conditions."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Sunny Day Playlist"}]}
        }

        handler = RecommendationHandler()

        # Simulate a different weather condition
        handler._last_weather_search_string = "sunny"
        media, items = handler.handling_weather_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert len(items) == 1
        assert items[0]["name"] == "Sunny Day Playlist"
