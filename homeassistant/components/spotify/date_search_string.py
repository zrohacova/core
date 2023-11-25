"""Contains HolidayDateMapper class, which provides functionality to map current holiday if there is one in the range of a week, otherwise to map current day, month and season to an appropriate search string to be entered in Spotify."""
import calendar
from datetime import date, datetime, timedelta
from typing import Any

import country_converter as coco
from deep_translator import GoogleTranslator
import geocoder
import requests

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .const import NO_HOLIDAY
from .recommendation_handling import get_entity_ids


class HolidayDateMapper:
    """A class to find the current holiday for a certain country and date, or season if there is no holiday."""

    def __init__(self) -> None:
        """Initialize of the HolidaySeasonMapper."""

        # Mapping of which months at which hemisphere corresponds to what season.
        self.season_hemisphere_mapping = {
            1: {"Northern": "Winter", "Southern": "Summer"},
            2: {"Northern": "Winter", "Southern": "Summer"},
            3: {"Northern": "Spring", "Southern": "Autumn"},
            4: {"Northern": "Spring", "Southern": "Autumn"},
            5: {"Northern": "Spring", "Southern": "Autumn"},
            6: {"Northern": "Summer", "Southern": "Winter"},
            7: {"Northern": "Summer", "Southern": "Winter"},
            8: {"Northern": "Summer", "Southern": "Winter"},
            9: {"Northern": "Autumn", "Southern": "Spring"},
            10: {"Northern": "Autumn", "Southern": "Spring"},
            11: {"Northern": "Autumn", "Southern": "Spring"},
            12: {"Northern": "Winter", "Southern": "Summer"},
        }

        # Mapping of the seasonal changes on the equator.
        self.season_equator_mapping = {...}

    def get_season(self, country_code: str, current_date: date):
        """Get the season in the given country on the given date."""
        month = current_date.month

        # Convert the country code to the corresponding country name
        country_name = coco.convert(country_code, to="name")
        if country_name == "not found":
            raise AttributeError(
                f"Country name not found for given country code {country_code}"
            )

        # Find the country zone which the country belongs to
        try:
            location_zone = self.locate_country_zone(country_name)

        except ValueError as e:
            raise ValueError(f"Error in locating the country zone: {e}") from e

        except ConnectionError as e:
            raise ConnectionError(f"Connection error during geocoding: {e}") from e

        # Get the corresponding seasons to the found country zone and month
        if location_zone == "Equator":
            ...
        else:
            hemispheres = self.season_hemisphere_mapping.get(month)
            if not hemispheres:
                raise ValueError(f"Provided {month} does not exist")

            season = hemispheres.get(location_zone)
            if not season:
                raise ValueError(f"No found season for location zone {location_zone}.")

        return season

    def locate_country_zone(self, country_name: str) -> str:
        """Identify the hemisphere in which the country is located or determine if it is situated on the equator."""

        # Get location information of the country given
        try:
            location = geocoder.osm(country_name)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Connection error during geocoding: {e}") from e

        # Extract the latitude from the location information of the country
        latitude = location.latlng[0]

        # Find the corresponding hemisphere from the latitudinal position
        if 0 < latitude <= 90:
            hemisphere = "Northern"
        elif -90 <= latitude < 0:
            hemisphere = "Southern"
        elif latitude == 0:
            hemisphere = "Equator"
        else:
            raise ValueError(f"No result found for the latitude {latitude}.")

        return hemisphere

    def get_current_holiday(self, hass: HomeAssistant):
        """Check if current date is in holiday range, then return current holiday."""
        current_date = dt_util.now().date()

        # Get holiday attributes
        calendar_entity_ids = get_entity_ids(hass, "calendar")
        if not calendar_entity_ids:
            return NO_HOLIDAY

        calendar_holiday_state = None
        holiday_start_time = None
        holiday_title = " "
        holiday_end_time = None

        # loop all calendar id's and check if it is a holiday calendar
        for entity_id in calendar_entity_ids:
            if self.is_holiday_calendar(entity_id):
                # get the next holiday of this calendar
                calendar_holiday_state = hass.states.get(entity_id)
                if calendar_holiday_state is None:
                    raise HomeAssistantError(
                        "Problem with fetching holidays for calendar", entity_id
                    )

                holiday = calendar_holiday_state.as_compressed_state["a"]

                if (
                    "start_time" not in holiday
                    or "message" not in holiday
                    or "end_time" not in holiday
                ):
                    raise HomeAssistantError(
                        "Your calendar with entity id ",
                        entity_id,
                        " is inactivated in your Google Calendar. Vists Google Calendar to activate it, or remove it from your HomeAssistant",
                    )

                start_time_this_holiday = datetime.strptime(
                    holiday["start_time"], "%Y-%m-%d %H:%M:%S"
                )

                if (
                    holiday_start_time is None
                    or holiday_start_time > start_time_this_holiday
                ):
                    holiday_start_time = start_time_this_holiday
                    holiday_end_time = datetime.strptime(
                        holiday["end_time"], "%Y-%m-%d %H:%M:%S"
                    )
                    holiday_title = holiday["message"]

        if calendar_holiday_state is None:
            return NO_HOLIDAY

        if holiday_end_time is None or holiday_start_time is None:
            raise HomeAssistantError(
                "Problem with fetching holiday dates for holiday", holiday_title
            )

        week_before_holiday = holiday_start_time.date() - timedelta(weeks=1)

        # Check if current date is in holiday range
        if week_before_holiday <= current_date <= holiday_end_time.date():
            return holiday_title

        return NO_HOLIDAY

    def is_holiday_calendar(self, calendar_id: str):
        """Check if the calendar is a calendar including holidays."""
        translator = GoogleTranslator()
        holiday_string = calendar_id.split(".")[1]
        translation = translator.translate(holiday_string)
        return "holiday" in translation.lower()

    def get_month(self, current_date: date):
        """Get month as a string."""
        current_month = current_date.month
        try:
            month_name = calendar.month_name[current_month]
            return month_name
        except IndexError:
            return "Invalid month number."

    def get_day_of_week(self, current_date: date):
        """Get day of week as a string."""
        current_month = current_date.month
        current_year = current_date.year
        current_day = current_date.day
        try:
            # Determine the day of the week
            day_number = calendar.weekday(current_year, current_month, current_day)
            day_name = calendar.day_name[day_number]
            return day_name
        except ValueError:
            return "Invalid date provided."

    def search_string_date(self, hass: HomeAssistant, user: Any):
        """Generate a search string for the date feature, if there is no holiday, the current season, month and day is returned, otherwise the current holiday."""
        current_date = dt_util.now().date()
        country = user["country"]

        if self.get_current_holiday(hass) == NO_HOLIDAY:
            return f"{self.get_season(country, current_date)}, {self.get_month(current_date)}, {self.get_day_of_week(current_date)}"

        return f"{self.get_current_holiday(hass)}"
