"""Module for testing the HolidayDateMapper functionality in the Spotify integration."""

import datetime
from unittest.mock import patch

import pytest

from homeassistant.components.spotify.date_search_string import HolidayDateMapper


@pytest.fixture
def holiday_date_mapper():
    """Fixture for initializing the HolidayDateMapper."""
    return HolidayDateMapper()


def test_init_valid_season_mapper(holiday_date_mapper: HolidayDateMapper) -> None:
    """Test initialization of HolidayDateMapper."""
    assert holiday_date_mapper.season_hemisphere_mapping is not None
    assert holiday_date_mapper.season_equator_mapping is not None


@patch("homeassistant.components.spotify.date_search_string.geocoder.osm")
def test_get_hemisphere(
    mock_geocoder_osm,
    holiday_date_mapper: HolidayDateMapper,
) -> None:
    """Test get accurate hemisphare based on latitude provided from mocking."""

    mock_location = mock_geocoder_osm.return_value
    mock_location.ok = True
    mock_location.latlng = (59.33258, 18.0649)

    hemisphere = holiday_date_mapper.locate_country_zone("Sweden")

    assert hemisphere == "Northern"


@patch("homeassistant.components.spotify.date_search_string.geocoder.osm")
def test_get_season(mock_geocoder_osm, holiday_date_mapper: HolidayDateMapper) -> None:
    """Test get correct season from given country and date."""
    mock_location = mock_geocoder_osm.return_value
    mock_location.ok = True
    mock_location.latlng = (-35.28346, 149.12807)

    date = datetime.date(year=2023, month=11, day=17)
    season = holiday_date_mapper.get_season("Australia", date)

    assert season == "Spring"


@patch("homeassistant.components.spotify.date_search_string.geocoder.osm")
def test_invalid_latitude_input(
    mock_geocoder_osm, holiday_date_mapper: HolidayDateMapper
) -> None:
    """Test that a ValueError is raised when an incorrect latitude is provided."""
    mock_location = mock_geocoder_osm.return_value
    mock_location.ok = True
    mock_location.latlng = (120, 149.12807)

    with pytest.raises(
        ValueError,
        match="No result found for the latitude 120.",
    ):
        holiday_date_mapper.locate_country_zone("Australia")
