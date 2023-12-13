"""Test Spotify browse media."""

from typing import Any
from unittest.mock import patch

from homeassistant.components.media_player.browse_media import BrowseMedia
from homeassistant.components.spotify.browse_media import build_item_response
from homeassistant.components.spotify.recommendation_handling import (
    RecommendationHandler,
)
from homeassistant.core import HomeAssistant

from tests.components.accuweather import init_integration


async def test_build_items_directories(hass: HomeAssistant) -> None:
    """Test browse media build items response method."""
    # directory
    TYPE = 0
    TITLE = 1

    directories = {
        0: ["current_user_playlists", "Playlists"],
        1: ["current_user_followed_artists", "Artists"],
        2: ["current_user_saved_albums", "Albums"],
        3: ["current_user_saved_tracks", "Tracks"],
        4: ["current_user_saved_shows", "Podcasts"],
        5: ["current_user_recently_played", "Recently played"],
        6: ["current_user_top_artists", "Top Artists"],
        7: ["current_user_top_tracks", "Top Tracks"],
        8: ["categories", "Categories"],
        9: ["featured_playlists", "Featured Playlists"],
        10: ["new_releases", "New Releases"],
    }

    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch("homeassistant.components.spotify.browse_media.Spotify"):
        user: dict[str, Any] = {"country": "SE"}
        can_play_artist = True

        assert spotify_mock
        assert user

        for _key, values in directories.items():
            exp_type = values[TYPE]
            exp_title = values[TITLE]

            payload = {
                "media_content_type": exp_type,
                "media_content_id": exp_type,
            }

            media: BrowseMedia = build_item_response(
                hass, spotify_mock, user, payload, can_play_artist=can_play_artist
            )

            assert media
            assert media.title == exp_title
            assert media.media_content_type == f"spotify://{exp_type}"
            assert media.media_content_id == exp_type
            assert media.media_class == "directory"


async def test_build_items_date(hass: HomeAssistant) -> None:
    """Testing browse media with date playlists."""
    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch.object(
        RecommendationHandler,
        "_generate_date_search_string",
        return_value="Test Playlist",
    ):
        user: dict[str, Any] = {"country": "SE"}
        can_play_artist = True

        assert spotify_mock
        assert user

        exp_type = "date_playlist"
        exp_title = "Date Playlists"

        payload = {
            "media_content_type": exp_type,
            "media_content_id": exp_type,
        }

        media: BrowseMedia = build_item_response(
            hass, spotify_mock, user, payload, can_play_artist=can_play_artist
        )

        assert media
        assert media.title == exp_title
        assert media.media_content_type == f"spotify://{exp_type}"
        assert media.media_content_id == exp_type
        assert media.media_class == "directory"


async def test_build_items_weather(hass: HomeAssistant) -> None:
    """Test browse media build items response method with weather."""
    await init_integration(hass, forecast=True)

    with patch(
        "homeassistant.components.spotify.config_flow.Spotify"
    ) as spotify_mock, patch(
        "homeassistant.components.accuweather.AccuWeather._async_get_data"
    ):
        user: dict[str, Any] = {"country": "SE"}
        can_play_artist = True

        assert spotify_mock
        assert user

        exp_type = "weather_playlist"
        exp_title = "Weather Playlists"

        payload = {
            "media_content_type": exp_type,
            "media_content_id": exp_type,
        }

        media: BrowseMedia = build_item_response(
            hass, spotify_mock, user, payload, can_play_artist=can_play_artist
        )

        assert media
        assert media.title == exp_title
        assert media.media_content_type == f"spotify://{exp_type}"
        assert media.media_content_id == exp_type
        assert media.media_class == "directory"
