"""Module for testing the HolidayDateMapper functionality in the Spotify integration."""
import datetime as dt
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from homeassistant.components.spotify.date_search_string import HolidayDateMapper
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError


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

    date = dt.date(year=2023, month=11, day=17)
    season = holiday_date_mapper.get_season("AU", date)

    assert season == "Spring"

    with pytest.raises(
        AttributeError, match="Country name not found for given country code  "
    ):
        holiday_date_mapper.get_season(" ", date)


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


def test_get_month(holiday_date_mapper: HolidayDateMapper) -> None:
    """Test correct month name is found."""
    # testing some random dates
    month_name = holiday_date_mapper.get_month(dt.date(year=2018, month=1, day=12))
    assert month_name == "January"

    month_name = holiday_date_mapper.get_month(dt.date(year=2021, month=4, day=28))
    assert month_name == "April"

    month_name = holiday_date_mapper.get_month(dt.date(year=2022, month=8, day=28))
    assert month_name == "August"

    month_name = holiday_date_mapper.get_month(dt.date(year=2021, month=10, day=28))
    assert month_name == "October"

    month_name = holiday_date_mapper.get_month(dt.date(year=2013, month=12, day=30))
    assert month_name == "December"

    with pytest.raises(
        ValueError,
        match=("month must be in 1..12"),
    ):
        month_name = holiday_date_mapper.get_month(dt.date(year=2013, month=13, day=30))


def test_get_day_of_week(holiday_date_mapper: HolidayDateMapper) -> None:
    """Test correct weekday name is found."""
    # testing some random dates
    weekday = holiday_date_mapper.get_day_of_week(dt.date(year=2020, month=2, day=11))
    assert weekday == "Tuesday"

    weekday = holiday_date_mapper.get_day_of_week(dt.date(year=2023, month=11, day=29))
    assert weekday == "Wednesday"

    weekday = holiday_date_mapper.get_day_of_week(dt.date(year=2013, month=8, day=31))
    assert weekday == "Saturday"


def test_no_google_calendar_setup(
    hass: HomeAssistant, holiday_date_mapper: HolidayDateMapper
) -> None:
    """Test that no holiday is returned when no google calendar is set up when fetching holidays."""
    result = holiday_date_mapper.get_current_holiday(hass)

    assert result == "No holiday"


@patch("homeassistant.components.spotify.date_search_string.GoogleTranslator.translate")
@patch(
    "homeassistant.components.spotify.date_search_string.RecommendationHandler.get_entity_ids"
)
def test_no_holiday_calendar(
    mock_get_entity_ids,
    mock_translate,
    hass: HomeAssistant,
    holiday_date_mapper: HolidayDateMapper,
) -> None:
    """Test that no holiday is returned when no holiday calendar is set up when fetching holidays."""
    mock_get_entity_ids.return_value = ["calendar.a_calendar"]
    mock_translate.return_value = "a_calendar"

    result = holiday_date_mapper.get_current_holiday(hass)

    assert result == "No holiday"


@patch("homeassistant.components.spotify.date_search_string.GoogleTranslator.translate")
def test_is_holiday_calendar(
    mock_translate, holiday_date_mapper: HolidayDateMapper
) -> None:
    """Test that calendars including holidays are detected as holiday calendars."""
    mock_translate.return_value = "week numbers"
    result = holiday_date_mapper.is_holiday_calendar("calendar.veckonummer")

    assert result is False

    mock_translate.return_value = "holidays_in_sweden"
    result = holiday_date_mapper.is_holiday_calendar("calendar.helgdagar_i_sverige")

    assert result is True


def test_is_holiday_in_range_no_state(holiday_date_mapper: HolidayDateMapper) -> None:
    """Test that holiday is not in range if no holiday state is found."""
    result = holiday_date_mapper.is_holiday_in_range(None, None, None, " ")
    assert result is False


def test_is_holiday_in_range_no_date(holiday_date_mapper: HolidayDateMapper) -> None:
    """Test that a HomeAssistantError is raised when dates for the holiday is not given."""
    holiday_title = "some holiday"
    calendar_state = State("calendar.some_calendar", "state")

    with pytest.raises(
        HomeAssistantError,
        match=(f"Problem with fetching holiday dates for holiday: {holiday_title}"),
    ):
        holiday_date_mapper.is_holiday_in_range(
            calendar_state, None, None, holiday_title
        )

    with pytest.raises(
        HomeAssistantError,
        match=(f"Problem with fetching holiday dates for holiday: {holiday_title}"),
    ):
        holiday_date_mapper.is_holiday_in_range(
            calendar_state, "2023-11-28", None, holiday_title
        )

    with pytest.raises(
        HomeAssistantError,
        match=(f"Problem with fetching holiday dates for holiday: {holiday_title}"),
    ):
        holiday_date_mapper.is_holiday_in_range(
            calendar_state, None, "2023-11-28", holiday_title
        )


@patch("homeassistant.components.spotify.date_search_string.dt_util.now")
def test_is_holiday_in_range(
    mock_today, holiday_date_mapper: HolidayDateMapper
) -> None:
    """Test if holiday is in weekly range."""
    # set today to 28 nov
    mock_today.return_value = datetime(2023, 11, 28, 12, 0, 0)

    holiday_title = "some holiday"
    calendar_state = State("calendar.some_calendar", "state")

    # if the holiday is today
    holiday_date = dt.date(year=2023, month=11, day=28)
    result = holiday_date_mapper.is_holiday_in_range(
        calendar_state, holiday_date, holiday_date, holiday_title
    )

    assert result is True

    # if the holiday is more than a week before
    holiday_date = dt.date(year=2023, month=11, day=13)
    result = holiday_date_mapper.is_holiday_in_range(
        calendar_state, holiday_date, holiday_date, holiday_title
    )

    assert result is False

    # if the holiday is more than a week later
    holiday_date = dt.date(year=2024, month=1, day=1)
    result = holiday_date_mapper.is_holiday_in_range(
        calendar_state, holiday_date, holiday_date, holiday_title
    )

    assert result is False


@patch("homeassistant.components.spotify.date_search_string.dt_util.now")
@patch("homeassistant.components.spotify.date_search_string.GoogleTranslator.translate")
@patch(
    "homeassistant.components.spotify.date_search_string.RecommendationHandler.get_entity_ids"
)
def test_get_current_holiday(
    mock_get_entity_ids,
    mock_translate,
    mock_today,
    holiday_date_mapper: HolidayDateMapper,
) -> None:
    """Test that a holiday title is returned if there is an upcoming holiday."""
    mock_get_entity_ids.return_value = ["calendar.a_holiday_calendar"]
    mock_translate.return_value = "a_holiday_calendar"
    mock_today.return_value = datetime(2023, 11, 9, 12, 0, 0)

    mock_hass = MagicMock()
    calendar_holiday_state = MagicMock()

    calendar_holiday_state.as_compressed_state = {
        "a": {
            "start_time": "2023-11-10 00:00:00",
            "message": "a holiday title",
            "end_time": "2023-11-10 00:00:00",
        }
    }

    with patch.object(mock_hass.states, "get") as mock_states_get:
        mock_states_get.return_value = calendar_holiday_state
        result = holiday_date_mapper.get_current_holiday(mock_hass)

        assert result == "a holiday title"


@patch("homeassistant.components.spotify.date_search_string.dt_util.now")
@patch("homeassistant.components.spotify.date_search_string.GoogleTranslator.translate")
@patch(
    "homeassistant.components.spotify.date_search_string.RecommendationHandler.get_entity_ids"
)
def test_get_next_holiday(
    mock_get_entity_ids,
    mock_translate,
    mock_today,
    holiday_date_mapper: HolidayDateMapper,
) -> None:
    """Test that the next holiday title is returned."""
    mock_get_entity_ids.return_value = [
        "calendar.a_holiday_calendar",
        "calendar.another_holiday_calendar",
    ]
    mock_translate.return_value = "holiday"

    mock_hass = MagicMock()

    # mock two holidays
    mock_calendar_holiday_state_1 = MagicMock()
    mock_calendar_holiday_state_1.as_compressed_state = {
        "a": {
            "start_time": "2023-11-10 00:00:00",
            "message": "a holiday title",
            "end_time": "2023-11-10 00:00:00",
        }
    }

    mock_calendar_holiday_state_2 = MagicMock()
    mock_calendar_holiday_state_2.as_compressed_state = {
        "a": {
            "start_time": "2023-12-25 00:00:00",
            "message": "another holiday title",
            "end_time": "2023-12-25 23:59:59",
        }
    }

    mock_today.return_value = datetime(2023, 11, 9, 12, 0, 0)

    with patch.object(mock_hass.states, "get") as mock_states_get:
        mock_states_get.side_effect = [
            mock_calendar_holiday_state_1,
            mock_calendar_holiday_state_2,
        ]
        result = holiday_date_mapper.get_current_holiday(mock_hass)

        assert result == "a holiday title"

        # change which holiday comes first
        mock_calendar_holiday_state_1.as_compressed_state = {
            "a": {
                "start_time": "2023-11-30 00:00:00",
                "message": "a holiday title",
                "end_time": "2023-11-30 00:00:00",
            }
        }
        mock_calendar_holiday_state_2.as_compressed_state = {
            "a": {
                "start_time": "2023-11-11 00:00:00",
                "message": "another holiday title",
                "end_time": "2023-11-11 23:59:59",
            }
        }

        mock_states_get.side_effect = [
            mock_calendar_holiday_state_1,
            mock_calendar_holiday_state_2,
        ]
        result = holiday_date_mapper.get_current_holiday(mock_hass)

        assert result == "another holiday title"
