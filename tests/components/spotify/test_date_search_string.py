"""Module for testing the HolidayDateMapper functionality in the Spotify integration."""

import datetime
from unittest.mock import patch

import pytest

from homeassistant.components.spotify.date_search_string import HolidayDateMapper
from homeassistant.core import HomeAssistant


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


def test_no_google_calendar_setup(
    hass: HomeAssistant, holiday_date_mapper: HolidayDateMapper
) -> None:
    """Test that no holiday is returned when no google calendar is set up when fetching holidays."""
    result = holiday_date_mapper.get_current_holiday(hass)

    assert result == "No holiday"


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
def test_search_string_date(
    mock_weekday,
    mock_month,
    mock_season,
    mock_holiday,
    hass: HomeAssistant,
    holiday_date_mapper: HolidayDateMapper,
) -> None:
    """Test generated search string."""
    mock_holiday.return_value = "Christmas Eve"
    mock_season.return_value = "Winter"
    mock_month.return_value = "December"
    mock_weekday.return_value = "Sunday"

    user = {"country": "a country"}

    result = holiday_date_mapper.search_string_date(hass, user)

    assert result == "Christmas Eve"

    mock_holiday.return_value = "No holiday"
    mock_season.return_value = "Summer"
    mock_month.return_value = "July"
    mock_weekday.return_value = "Friday"

    user = {"country": "a country"}

    result = holiday_date_mapper.search_string_date(hass, user)

    assert result == "Summer July Friday"
