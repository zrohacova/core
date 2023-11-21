"""Test Spotify Recommendation Handler."""

from unittest.mock import patch

import pytest
from spotipy.exceptions import SpotifyException

from homeassistant.components.spotify.recommendation_handling import (
    BROWSE_LIMIT,
    RecommendationHandler,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util


async def test_singleton_pattern(hass: HomeAssistant) -> None:
    """Test that the RecommendationHandler follows the singleton pattern."""
    handler1 = RecommendationHandler()
    handler2 = RecommendationHandler()
    assert handler1 is handler2


async def test_generate_date_search_string(hass: HomeAssistant) -> None:
    """Test the generation of date-based search strings."""
    handler = RecommendationHandler()
    with patch("homeassistant.util.dt.now") as mock_now:
        # Example: Test for a specific date
        mock_now.return_value = dt_util.now().replace(month=12, day=25)
        search_string = handler._generate_date_search_string()
        assert (
            search_string == "winter"
        )  # Assuming "winter" is the search string for December


async def test_is_new_date(hass: HomeAssistant) -> None:
    """Test the check for a new date."""
    handler = RecommendationHandler()
    handler._last_api_call_date = "2020-12-24"
    assert handler._is_new_date("2020-12-25")  # New date
    assert not handler._is_new_date("2020-12-24")  # Same date


async def test_fetch_spotify_playlists(hass: HomeAssistant) -> None:
    """Test fetching playlists from Spotify."""
    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Test Playlist"}]}
        }

        handler = RecommendationHandler()
        media, items = handler._fetch_spotify_playlists(
            spotify_mock, "Test", "2020-12-25"
        )

        assert spotify_mock.search.called
        assert len(items) == 1
        assert items[0]["name"] == "Test Playlist"


async def test_handling_date_recommendations_with_mocked_date(
    hass: HomeAssistant,
) -> None:
    """Test handling date recommendations with a mocked current date."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Christmas Playlist",
    ):
        handler = RecommendationHandler()
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Christmas Playlist"}]}
        }

        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert spotify_mock.search.call_args[1]["q"] == "Christmas Playlist"
        assert len(items) == 1
        assert items[0]["name"] == "Christmas Playlist"


async def test_handling_date_recommendations_empty_playlist(
    hass: HomeAssistant,
) -> None:
    """Test handling date recommendations with an empty playlist response and check error message."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Empty Playlist",
    ):
        spotify_mock.search.return_value = {"playlists": {"items": []}}

        handler = RecommendationHandler()
        handler._last_api_call_date = ""

        with pytest.raises(HomeAssistantError) as excinfo:
            media, items = handler.handling_date_recommendations(hass, spotify_mock)
        assert "There was an issue with fetching the playlists" in str(excinfo.value)


async def test_handling_date_recommendations_api_error(hass: HomeAssistant) -> None:
    """Test handling date recommendations with an API error."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler, "_generate_date_search_string", return_value="API Error"
    ):
        spotify_mock.search.side_effect = SpotifyException(
            http_status=500, code=-1, msg="API Error"
        )

        handler = RecommendationHandler()
        handler._last_api_call_date = "2020-06-01"

        try:
            media, items = handler.handling_date_recommendations(hass, spotify_mock)
            pytest.fail()
        except HomeAssistantError:
            assert spotify_mock.search.called


async def test_handling_date_recommendations_caching(hass: HomeAssistant) -> None:
    """Test caching mechanism in date recommendations."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Winter Playlist",
    ):
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Winter Playlist"}]}
        }

        handler = RecommendationHandler()

        # First call
        handler.handling_date_recommendations(hass, spotify_mock)
        spotify_mock.search.assert_called_once()

        # Reset mock call count
        spotify_mock.search.reset_mock()

        # Second call with the same date
        handler.handling_date_recommendations(hass, spotify_mock)
        assert not spotify_mock.search.called


async def test_handling_api_unexpected_response(hass: HomeAssistant) -> None:
    """Test handling unexpected response structure from Spotify API."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Unexpected Response",
    ):
        spotify_mock.search.return_value = {"unexpected_key": "unexpected_value"}

        handler = RecommendationHandler()
        handler._last_api_call_date = "2023-11-20"

        with pytest.raises(HomeAssistantError):
            _, _ = handler.handling_date_recommendations(hass, spotify_mock)


async def test_handling_different_dates(hass: HomeAssistant) -> None:
    """Test handling different dates for recommendations."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Different Date Playlist",
    ):
        handler = RecommendationHandler()
        handler._last_api_call_date = "2023-11-19"  # Previous date
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Different Date Playlist"}]}
        }

        media, items = handler.handling_date_recommendations(hass, spotify_mock)

        assert spotify_mock.search.called
        assert spotify_mock.search.call_args[1]["q"] == "Different Date Playlist"
        assert len(items) == 1
        assert items[0]["name"] == "Different Date Playlist"


async def test_handling_malformed_data_missing_key(hass: HomeAssistant) -> None:
    """Test handling date recommendations with malformed data missing expected key."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Malformed Data",
    ):
        spotify_mock.search.return_value = {"playlists": {}}  # Missing 'items' key

        handler = RecommendationHandler()
        handler._last_api_call_date = "2023-11-20"

        with pytest.raises(HomeAssistantError):
            _, _ = handler.handling_date_recommendations(hass, spotify_mock)


async def test_handling_api_rate_limit_and_downtime(hass: HomeAssistant) -> None:
    """Test handling API rate limit and downtime."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="API Downtime",
    ):
        spotify_mock.search.side_effect = SpotifyException(
            http_status=429, code=-1, msg="Rate Limit Exceeded"
        )

        handler = RecommendationHandler()
        handler._last_api_call_date = "2023-11-20"

        with pytest.raises(HomeAssistantError):
            media, items = handler.handling_date_recommendations(hass, spotify_mock)


async def test_handling_excess_items_from_spotify(hass: HomeAssistant) -> None:
    """Test handling more items than BROWSE_LIMIT from Spotify."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Excess Items",
    ):
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": f"Playlist {i}"} for i in range(100)]}
        }

        handler = RecommendationHandler()
        handler._last_api_call_date = "2023-11-20"

        media, items = handler.handling_date_recommendations(hass, spotify_mock)
        assert len(items) <= BROWSE_LIMIT
