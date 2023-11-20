"""Module for testing the WeatherPlaylistMapper functionality in the Spotify integration."""

import datetime
import json
from unittest.mock import patch

import pytest

# from homeassistant.components.spotify.search_string_generator import HolidaySeasonMapper
from homeassistant.components.spotify.search_string_generator import (
    HolidaySeasonMapper,
    WeatherPlaylistMapper,
)


# Fixture to load the test JSON data
@pytest.fixture
def spotify_mapping_data():
    """Fixture for creating a WeatherPlaylistMapper instance with a valid mapping file."""
    with open(
        "homeassistant/components/spotify/spotify_mappings.json", encoding="utf-8"
    ) as file:
        return json.load(file)


# Fixture for initializing the WeatherPlaylistMapper with test data
@pytest.fixture
def mapper(spotify_mapping_data):
    """Fixture for initializing the WeatherPlaylistMapper with test data."""
    # Write the test data to a test file
    with open(
        "tests/components/spotify/test_spotify_mappings.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(spotify_mapping_data, file, indent=2)
    # Initialize the mapper with the path to the test file
    return WeatherPlaylistMapper("tests/components/spotify/test_spotify_mappings.json")


def test_init_valid_file(mapper: WeatherPlaylistMapper) -> None:
    """Test initializing WeatherPlaylistMapper with a valid mapping file."""
    assert mapper.spotify_category_mapping is not None


def test_init_invalid_file() -> None:
    """Test initializing WeatherPlaylistMapper with an invalid mapping file."""
    with pytest.raises(FileNotFoundError):
        WeatherPlaylistMapper(
            "homeassistant/components/spotify/test_spotify_mappings.json"
        )


def test_map_weather_to_playlists_valid_conditions(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping weather conditions to search string with valid conditions."""
    search_string = mapper.map_weather_to_playlists(20, "pouring")
    # Expected for 'warm' 'pouring'
    assert search_string == "Rainy Day Rhythms"


def test_map_weather_to_playlists_invalid_condition(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping weather conditions to search string with an invalid condition."""
    with pytest.raises(ValueError):
        mapper.map_weather_to_playlists(20, "sleepy")


def test_map_weather_to_playlists_boundary_temperature_1(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping weather conditions to search string at the boundary temperature."""
    search_string = mapper.map_weather_to_playlists(15, "cloudy")
    # Expected for 'warm' 'cloudy
    assert search_string == "Overcast Moods"


def test_map_weather_to_playlists_boundary_temperature_2(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping at boundary temperature values."""
    search_string = mapper.map_weather_to_playlists(0, "fog")
    # Expected for 'cold' 'fog'
    assert search_string == "Foggy Night Chill"


def test_map_weather_to_playlists_negative_temperature(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with negative temperature."""
    search_string = mapper.map_weather_to_playlists(-5, "snowy")
    # Expected for 'cold' 'snowy'
    assert search_string == "Blizzard Ballads"


def test_map_weather_to_playlists_high_temperature(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with high temperature."""
    search_string = mapper.map_weather_to_playlists(35, "fog")
    # Expected for 'warm' 'fog'
    assert search_string == "Misty Morning Mix"


def test_map_weather_to_playlists_unusual_condition(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with unusual weather condition."""
    search_string = mapper.map_weather_to_playlists(20, "exceptional")
    # Expected for 'warm' 'exceptional'
    assert search_string == "Extraordinary Sounds"


def test_map_weather_to_playlists_non_standard_condition_string(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with non-standard condition strings."""
    search_string = mapper.map_weather_to_playlists(20, "   SUNNY   ")
    # Expected for 'warm' 'sunny'
    assert search_string == "Sunny Day Play"


def test_map_weather_to_playlists_large_temperature(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with large temperature values."""
    search_string = mapper.map_weather_to_playlists(100, "lightning")
    # Expected for 'warm' 'lightning'
    assert search_string == "Electric Summer"


def test_upper_case_input(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test condition input with only upper case letters."""
    search_string = mapper.map_weather_to_playlists(20, "RAINY")
    # Expected for 'warm' 'rainy'
    assert search_string == "Raindrops and Beats"


def test_map_weather_to_playlists_null_parameters(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with null or missing parameters."""
    with pytest.raises(TypeError):
        mapper.map_weather_to_playlists(None, "sunny")


def test_condtion_including_special_characters(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test failing when provided condition with special characters in it."""
    with pytest.raises(ValueError):
        mapper.map_weather_to_playlists(20, "windy?")


@pytest.fixture
def holiday_season_mapper():
    """Fixture for initializing the HolidaySeasonMapper."""
    return HolidaySeasonMapper()


def test_init_valid_season_mapper(holiday_season_mapper: HolidaySeasonMapper) -> None:
    """Test initialization of HolidaySeasonMapper."""
    assert holiday_season_mapper.season_hemisphere_mapping is not None
    assert holiday_season_mapper.season_equator_mapping is not None


@patch("homeassistant.components.spotify.search_string_generator.geocoder.osm")
def test_get_hemisphere(
    mock_geocoder_osm,
    holiday_season_mapper: HolidaySeasonMapper,
) -> None:
    """Test get accurate hemisphare based on latitude provided from mocking."""

    mock_location = mock_geocoder_osm.return_value
    mock_location.ok = True
    mock_location.latlng = (59.33258, 18.0649)

    hemisphere = holiday_season_mapper.locate_country_zone("Sweden")

    assert hemisphere == "Northern"


@patch("homeassistant.components.spotify.search_string_generator.geocoder.osm")
def test_get_season(
    mock_geocoder_osm, holiday_season_mapper: HolidaySeasonMapper
) -> None:
    """Test get correct season from given country and date."""
    mock_location = mock_geocoder_osm.return_value
    mock_location.ok = True
    mock_location.latlng = (-35.28346, 149.12807)

    date = datetime.date(year=2023, month=11, day=17)
    season = holiday_season_mapper.get_season("Australia", date)

    assert season == "Spring"


@patch("homeassistant.components.spotify.search_string_generator.geocoder.osm")
def test_invalid_latitude_input(
    mock_geocoder_osm, holiday_season_mapper: HolidaySeasonMapper
) -> None:
    """Test that a ValueError is raised when an incorrect latitude is provided."""
    mock_location = mock_geocoder_osm.return_value
    mock_location.ok = True
    mock_location.latlng = (120, 149.12807)

    with pytest.raises(
        ValueError,
        match="No result found for the latitude 120.",
    ):
        holiday_season_mapper.locate_country_zone("Australia")
