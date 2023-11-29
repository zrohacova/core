"""Module for testing the WeatherPlaylistMapper functionality in the Spotify integration."""

import json

import pytest

from homeassistant.components.spotify.weather_search_string import WeatherPlaylistMapper


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
    search_string = mapper.map_weather_to_playlists(20, "pouring", "celsius")
    # Expected for 'warm' 'pouring'
    assert search_string == "Rainy Day Rhythms"


def test_map_weather_to_playlists_invalid_condition(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping weather conditions to search string with an invalid condition."""
    with pytest.raises(ValueError):
        mapper.map_weather_to_playlists(20, "sleepy", "celsius")


def test_map_weather_to_playlists_boundary_temperature_1(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping weather conditions to search string at the boundary temperature."""
    search_string = mapper.map_weather_to_playlists(15, "cloudy", "celsius")
    # Expected for 'warm' 'cloudy
    assert search_string == "Overcast Moods"


def test_map_weather_to_playlists_boundary_temperature_2(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping at boundary temperature values."""
    search_string = mapper.map_weather_to_playlists(0, "fog", "celsius")
    # Expected for 'cold' 'fog'
    assert search_string == "Foggy Night Chill"


def test_map_weather_to_playlists_negative_temperature(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with negative temperature."""
    search_string = mapper.map_weather_to_playlists(-5, "snowy", "celsius")
    # Expected for 'cold' 'snowy'
    assert search_string == "Blizzard Ballads"


def test_map_weather_to_playlists_high_temperature(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with high temperature."""
    search_string = mapper.map_weather_to_playlists(35, "fog", "celsius")
    # Expected for 'warm' 'fog'
    assert search_string == "Misty Morning Mix"


def test_map_weather_to_playlists_unusual_condition(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with unusual weather condition."""
    search_string = mapper.map_weather_to_playlists(20, "exceptional", "celsius")
    # Expected for 'warm' 'exceptional'
    assert search_string == "Extraordinary Sounds"


def test_map_weather_to_playlists_non_standard_condition_string(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with non-standard condition strings."""
    search_string = mapper.map_weather_to_playlists(20, "   SUNNY   ", "celsius")
    # Expected for 'warm' 'sunny'
    assert search_string == "Sunny Day Play"


def test_upper_case_input(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test condition input with only upper case letters."""
    search_string = mapper.map_weather_to_playlists(20, "RAINY", "celsius")
    # Expected for 'warm' 'rainy'
    assert search_string == "Raindrops and Beats"


def test_map_weather_to_playlists_null_parameters(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping with null or missing parameters."""
    with pytest.raises(TypeError):
        mapper.map_weather_to_playlists(None, "sunny", "celsius")


def test_condtion_including_special_characters(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test failing when provided condition with special characters in it."""
    with pytest.raises(ValueError):
        mapper.map_weather_to_playlists(20, "windy?", "celsius")


def test_map_weather_to_playlists_fahrenheit_temperature_unit_high(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping weather conditions to search string with Fahrenheit temperature unit (high)."""
    search_string = mapper.map_weather_to_playlists(68, "sunny", "fahrenheit")
    # Expected for 'warm' 'sunny'
    assert search_string == "Sunny Day Play"


def test_map_weather_to_playlists_fahrenheit_temperature_unit_low(
    mapper: WeatherPlaylistMapper,
) -> None:
    """Test mapping weather conditions to search string with Fahrenheit temperature unit (low)."""
    search_string = mapper.map_weather_to_playlists(21, "snowy", "fahrenheit")
    # Expected for 'cold' 'snowy'
    assert search_string == "Blizzard Ballads"
