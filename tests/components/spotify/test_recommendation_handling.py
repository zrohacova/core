"""Test Spotify Recommendation Handler."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from spotipy.exceptions import SpotifyException

from homeassistant.components.spotify.const import NO_HOLIDAY
from homeassistant.components.spotify.recommendation_handling import (
    BROWSE_LIMIT,
    RecommendationHandler,
    RecommendedPlaylistDomains,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from tests.components.accuweather import init_integration

SPOTIFY_MOCK_PATH = "homeassistant.components.spotify.config_flow.Spotify"


@patch(
    "homeassistant.components.spotify.recommendation_handling.RecommendationHandler._has_weather_changed"
)
async def test_handling_weather_recommendations(
    mock_has_weather_changed, hass: HomeAssistant
) -> None:
    """Test handling weather recommendations."""
    handler = RecommendationHandler()
    await init_integration(hass)

    mock_has_weather_changed.return_value = True

    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch(
        SPOTIFY_MOCK_PATH
    ) as spotify_mock, patch.object(
        handler,
        "_get_current_weather_search_string",
        return_value="Cold Sunny",
    ):
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


async def test_no_weather_available(hass: HomeAssistant) -> None:
    """Test handling no setup weather integration."""
    handler = RecommendationHandler()

    with patch(SPOTIFY_MOCK_PATH) as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {
                "items": [
                    {"name": "Sunny Day Playlist 1", "id": "playlist_id_1"},
                    {"name": "Sunny Day Playlist 2", "id": "playlist_id_2"},
                ]
            }
        }

        with pytest.raises(HomeAssistantError):
            handler.handling_weather_recommendations(hass, spotify_mock)


async def test_singleton_pattern() -> None:
    """Test that the RecommendationHandler follows the singleton pattern."""
    handler1 = RecommendationHandler()
    handler2 = RecommendationHandler()
    assert handler1 is handler2


@patch(
    "homeassistant.components.spotify.recommendation_handling.RecommendationHandler.get_entity_ids"
)
@patch(
    "homeassistant.components.spotify.date_search_string.HolidayDateMapper.get_current_holiday"
)
@patch(
    "homeassistant.components.spotify.date_search_string.HolidayDateMapper.get_season"
)
@patch(
    "homeassistant.components.spotify.date_search_string.HolidayDateMapper.get_month"
)
@patch(
    "homeassistant.components.spotify.date_search_string.HolidayDateMapper.get_day_of_week"
)
async def test_generate_date_search_string(
    mock_weekday,
    mock_month,
    mock_season,
    mock_holiday,
    mock_get_entity_ids,
    hass: HomeAssistant,
) -> None:
    """Test the connection of modules resposinble for generation of date-based search strings."""
    mock_get_entity_ids.return_value = ["calendar.a_calendar"]
    mock_holiday.return_value = "Christmas Eve"
    mock_season.return_value = "Summer"
    mock_month.return_value = "December"
    mock_weekday.return_value = "Sunday"

    handler = RecommendationHandler()

    with patch("homeassistant.util.dt.now") as mock_now, patch(
        "homeassistant.components.spotify.recommendation_handling.Spotify"
    ) as spotify_mock:
        user: dict[str, Any] = {"country": "AU"}

        assert spotify_mock
        assert user

        mock_now.return_value = dt_util.now().replace(month=12, day=25)

        search_string = handler._generate_date_search_string(hass, user)

        assert search_string == "Christmas Eve"


@patch(
    "homeassistant.components.spotify.recommendation_handling.RecommendationHandler.get_entity_ids"
)
@patch(
    "homeassistant.components.spotify.date_search_string.HolidayDateMapper.get_current_holiday"
)
@patch(
    "homeassistant.components.spotify.date_search_string.HolidayDateMapper.get_season"
)
@patch(
    "homeassistant.components.spotify.date_search_string.HolidayDateMapper.get_month"
)
@patch(
    "homeassistant.components.spotify.date_search_string.HolidayDateMapper.get_day_of_week"
)
async def test_generate_search_string_error_propagation(
    mock_weekday,
    mock_month,
    mock_season,
    mock_holiday,
    mock_get_entity_ids,
    hass: HomeAssistant,
) -> None:
    """Test that raised errors are handled correctly when propagated between modules."""
    mock_get_entity_ids.return_value = ["calendar.a_calendar"]
    mock_holiday.return_value = NO_HOLIDAY
    mock_season.return_value = "Summer"
    mock_month.return_value = "July"
    mock_weekday.return_value = "Sunday"

    handler = RecommendationHandler()

    with pytest.raises(ValueError):
        handler._generate_date_search_string(hass, None)


async def test_is_new_date(hass: HomeAssistant) -> None:
    """Test the check for a new date."""
    handler = RecommendationHandler()
    handler._last_api_call_date = "2020-12-24"
    assert handler._is_new_date("2020-12-25")
    assert not handler._is_new_date("2020-12-24")


async def test_fetch_spotify_playlists(hass: HomeAssistant) -> None:
    """Test fetching playlists from Spotify."""
    with patch(SPOTIFY_MOCK_PATH) as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Test Playlist"}]}
        }

        handler = RecommendationHandler()
        _, items = handler._fetch_spotify_playlists(spotify_mock, "Test", "2020-12-25")

        assert spotify_mock.search.called
        assert len(items) == 1
        assert items[0]["name"] == "Test Playlist"


async def test_handling_date_recommendations_with_mocked_date(
    hass: HomeAssistant,
) -> None:
    """Test handling date recommendations with a mocked current date."""
    playlist_name = "Christmas Playlist"
    user: dict[str, Any] = {"country": "SE"}

    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value=playlist_name,
    ):
        handler = RecommendationHandler()
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": playlist_name}]}
        }

        _, items = handler.handling_date_recommendations(spotify_mock, hass, user)

        assert spotify_mock.search.called
        assert spotify_mock.search.call_args[1]["q"] == playlist_name
        assert len(items) == 1
        assert items[0]["name"] == playlist_name


async def test_handling_date_recommendations_empty_playlist(
    hass: HomeAssistant,
) -> None:
    """Test handling date recommendations with an empty playlist response and check error message."""
    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Empty Playlist",
    ):
        spotify_mock.search.return_value = {"playlists": {"items": []}}

        handler = RecommendationHandler()
        handler._last_api_call_date = ""

        with pytest.raises(HomeAssistantError) as excinfo:
            _, _ = handler.handling_date_recommendations(
                spotify_mock, hass, user={"country": "SE"}
            )
        assert "There was an issue with fetching the playlists" in str(excinfo.value)


async def test_handling_date_recommendations_api_error(hass: HomeAssistant) -> None:
    """Test handling date recommendations with an API error."""
    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch.object(
        RecommendationHandler, "_generate_date_search_string", return_value="API Error"
    ):
        spotify_mock.search.side_effect = SpotifyException(
            http_status=500, code=-1, msg="API Error"
        )

        handler = RecommendationHandler()
        handler._last_api_call_date = "2020-06-01"

        try:
            _, _ = handler.handling_date_recommendations(
                spotify_mock, hass, user={"country": "SE"}
            )
            pytest.fail()
        except HomeAssistantError:
            assert spotify_mock.search.called


async def test_handling_date_recommendations_caching(hass: HomeAssistant) -> None:
    """Test caching mechanism in date recommendations."""
    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Winter Playlist",
    ):
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": "Winter Playlist"}]}
        }

        handler = RecommendationHandler()

        handler.handling_date_recommendations(
            spotify_mock, hass, user={"country": "SE"}
        )
        spotify_mock.search.assert_called_once()

        spotify_mock.search.reset_mock()

        handler.handling_date_recommendations(
            spotify_mock, hass, user={"country": "SE"}
        )
        assert not spotify_mock.search.called


async def test_handling_api_unexpected_response(hass: HomeAssistant) -> None:
    """Test handling unexpected response structure from Spotify API."""
    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Unexpected Response",
    ):
        spotify_mock.search.return_value = {"unexpected_key": "unexpected_value"}

        handler = RecommendationHandler()
        handler._last_api_call_date = "2023-11-20"

        with pytest.raises(HomeAssistantError):
            _, _ = handler.handling_date_recommendations(
                spotify_mock, hass, user={"country": "SE"}
            )


async def test_handling_different_dates(hass: HomeAssistant) -> None:
    """Test handling different dates for recommendations."""
    playlist_name = "Autumn Playlist"

    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value=playlist_name,
    ):
        handler = RecommendationHandler()
        handler._last_api_call_date = "2023-11-19"
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": playlist_name}]}
        }

        _, items = handler.handling_date_recommendations(
            spotify_mock, hass, user={"country": "SE"}
        )

        assert spotify_mock.search.called
        assert spotify_mock.search.call_args[1]["q"] == playlist_name
        assert len(items) == 1
        assert items[0]["name"] == playlist_name


async def test_handling_malformed_data_missing_key(hass: HomeAssistant) -> None:
    """Test handling date recommendations with malformed data missing expected key."""
    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Malformed Data",
    ):
        spotify_mock.search.return_value = {"playlists": {}}

        handler = RecommendationHandler()
        handler._last_api_call_date = "2023-11-20"

        with pytest.raises(HomeAssistantError):
            _, _ = handler.handling_date_recommendations(
                spotify_mock, hass, user={"country": "SE"}
            )


async def test_handling_api_rate_limit_and_downtime(hass: HomeAssistant) -> None:
    """Test handling API rate limit and downtime."""
    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch.object(
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
            _, _ = handler.handling_date_recommendations(
                spotify_mock, hass, user={"country": "SE"}
            )


async def test_handling_excess_items_from_spotify(hass: HomeAssistant) -> None:
    """Test handling more items than BROWSE_LIMIT from Spotify."""
    with patch(SPOTIFY_MOCK_PATH) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Excess Items",
    ):
        spotify_mock.search.return_value = {
            "playlists": {"items": [{"name": f"Playlist {i}"} for i in range(100)]}
        }

        handler = RecommendationHandler()
        handler._last_api_call_date = "2023-11-20"

        _, items = handler.handling_date_recommendations(
            spotify_mock, hass, user={"country": "SE"}
        )
        assert len(items) <= BROWSE_LIMIT


@patch("homeassistant.components.spotify.recommendation_handling.er.async_get")
def test_get_entity_ids(mock_async_get, hass: HomeAssistant) -> None:
    """Test entity id's of given domain is returned."""

    mock_entity_reg = MagicMock()
    mock_async_get.return_value = mock_entity_reg

    # test with one calendar entity

    mock_entity_reg.entities.values.return_value = [
        MagicMock(
            entity_id="an_entity_id", domain=RecommendedPlaylistDomains.CALENDAR.value
        )
    ]

    entity_ids = RecommendationHandler.get_entity_ids(
        hass, RecommendedPlaylistDomains.CALENDAR
    )

    mock_async_get.assert_called_once_with(hass)
    mock_entity_reg.entities.values.assert_called_once()
    assert len(entity_ids) == 1

    # test with two entities with matching domains

    mock_entity_reg.entities.values.return_value = [
        MagicMock(
            entity_id="an_entity_id", domain=RecommendedPlaylistDomains.CALENDAR.value
        ),
        MagicMock(
            entity_id="another_entity_id",
            domain=RecommendedPlaylistDomains.CALENDAR.value,
        ),
    ]

    entity_ids = RecommendationHandler.get_entity_ids(
        hass, RecommendedPlaylistDomains.CALENDAR
    )
    assert len(entity_ids) == 2

    # test with one matching entity domain, and two other entities (one of a non-matching domain and one with no domain)

    mock_entity_reg.entities.values.return_value = [
        MagicMock(
            entity_id="an_entity_id", domain=RecommendedPlaylistDomains.CALENDAR.value
        ),
        MagicMock(
            entity_id="another_entity_id",
            domain=RecommendedPlaylistDomains.WEATHER.value,
        ),
        MagicMock(entity_id="a_third_entity_id"),
    ]

    entity_ids = RecommendationHandler.get_entity_ids(
        hass, RecommendedPlaylistDomains.CALENDAR
    )
    assert len(entity_ids) == 1

    # test with no matching entity domain

    mock_entity_reg.entities.values.return_value = [
        MagicMock(
            entity_id="an_entity_id", domain=RecommendedPlaylistDomains.WEATHER.value
        )
    ]

    entity_ids = RecommendationHandler.get_entity_ids(
        hass, RecommendedPlaylistDomains.CALENDAR
    )
    assert len(entity_ids) == 0

    # test with one weather entity

    mock_entity_reg.entities.values.return_value = [
        MagicMock(
            entity_id="an_entity_id", domain=RecommendedPlaylistDomains.WEATHER.value
        )
    ]

    entity_ids = RecommendationHandler.get_entity_ids(
        hass, RecommendedPlaylistDomains.WEATHER
    )
    assert len(entity_ids) == 1

    # test with no entities

    mock_entity_reg.entities.values.return_value = []

    entity_ids = RecommendationHandler.get_entity_ids(
        hass, RecommendedPlaylistDomains.WEATHER
    )
    assert len(entity_ids) == 0
