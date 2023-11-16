"""Test Spotify Recommendation Handler."""

from datetime import timedelta
from unittest.mock import patch

from spotipy.exceptions import SpotifyException

from homeassistant.components.spotify.recommendation_handling import (
    RecommendationHandler,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util


async def test_singleton_pattern(hass: HomeAssistant):
    """Test that the RecommendationHandler follows the singleton pattern."""
    handler1 = RecommendationHandler()
    handler2 = RecommendationHandler()
    assert handler1 is handler2


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


async def test_handling_date_recommendations(hass: HomeAssistant) -> None:
    """Test handling date recommendations."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Winter Playlist"}]}
        }

        handler = RecommendationHandler()
        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert len(items) == 1
        assert items[0]["name"] == "Winter Playlist"
        assert media is not None


async def test_handling_date_recommendations_empty_playlist(
    hass: HomeAssistant,
) -> None:
    """Test handling date recommendations with an empty playlist response."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {"playlists": {"items": []}}

        handler = RecommendationHandler()
        # Reset the last API call date to ensure the search method is called
        handler._last_api_call_date = ""
        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert items == []
        assert media is not None


async def test_handling_date_recommendations_api_error(hass: HomeAssistant) -> None:
    """Test handling date recommendations with an API error."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.side_effect = SpotifyException(
            http_status=500, code=-1, msg="API Error"
        )

        handler = RecommendationHandler()
        # Reset or change the last API call date to ensure the search method is called
        handler._last_api_call_date = "2020-06-01"
        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called


async def test_handling_date_recommendations_caching(hass: HomeAssistant) -> None:
    """Test caching mechanism in date recommendations."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Winter Playlist"}]}
        }

        handler = RecommendationHandler()

        # First call
        handler.handling_date_recommendations(hass, spotify_mock)
        assert spotify_mock.search.called_once

        # Reset mock call count
        spotify_mock.search.reset_mock()

        # Second call with the same date
        handler.handling_date_recommendations(hass, spotify_mock)
        assert not spotify_mock.search.called


async def test_handling_different_dates(hass: HomeAssistant) -> None:
    """Test handling different dates."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Summer Playlist"}]}
        }

        handler = RecommendationHandler()

        previous_date = (dt_util.now().date() - timedelta(days=1)).isoformat()
        handler._last_api_call_date = previous_date
        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert len(items) == 1
        assert items[0]["name"] == "Summer Playlist"


async def test_handling_invalid_date_format(hass: HomeAssistant) -> None:
    """Test handling date recommendations with an invalid date format."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {"playlists": {"items": []}}

        handler = RecommendationHandler()

        # Set an invalid date
        handler._last_api_call_date = "invalid-date"

        # Call the method and expect an API call
        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        # Check that the API was called due to invalid date
        assert spotify_mock.search.called
        assert items == []
        assert media is not None


async def test_handling_malformed_data_from_spotify(hass: HomeAssistant) -> None:
    """Test handling malformed data from Spotify API."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        malformed_data = {"unexpected_key": "unexpected_value"}
        spotify_mock.search.return_value = malformed_data

        handler = RecommendationHandler()
        handler._last_api_call_date = "2020-06-01"

        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        # Check that the API was called and verify the returned data
        assert spotify_mock.search.called
        assert media == malformed_data  # Expecting the raw response
        assert items == []  # No items extracted from the malformed data


async def test_handling_api_rate_limit(hass: HomeAssistant) -> None:
    """Test handling Spotify API rate limit."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.side_effect = SpotifyException(
            http_status=429, code=-1, msg="Rate limit exceeded"
        )

        handler = RecommendationHandler()
        # Reset or change the last API call date to ensure the search method is called
        handler._last_api_call_date = "2020-06-01"
        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert items == []
        assert media is None


async def test_handling_api_downtime(hass: HomeAssistant) -> None:
    """Test handling Spotify API downtime or unavailability."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.side_effect = SpotifyException(
            http_status=503, code=-1, msg="Service Unavailable"
        )

        handler = RecommendationHandler()
        # Reset or change the last API call date to ensure the search method is called
        handler._last_api_call_date = "2020-06-01"
        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert items == []
        assert media is None
