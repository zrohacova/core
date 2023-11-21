"""Contains HolidayDateMapper class, which provides functionality to map weather conditions and temperature ranges to an appropriate search string to be entered in Spotify."""
import calendar
import contextlib
from datetime import date, timedelta

import geocoder

# from googletrans import Translator
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util


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

    # FIX: what is the type for the date provided? Will we need to check that it has the correct form?
    def get_holiday_or_season(self, country: str, current_date: date):
        """Get the holiday in the country for the specified date. If there is no holiday in the given country on that date, the season is retrieved.

        Args:
            country (str): The country to find the holiday or season for.
            current_date (FIX): The current date.

        Returns:
            str: The holiday for the given date in the given country, or the season based on the date and country if there is no holiday.

        Raises:
            FIX
        """

        # Find the season in the country at given date (if no holiday was found)
        season = self.get_season(country, current_date)

        return season

    # FIX correct error handling? Need to catch exceptions?
    # FIX The country code will be given, not the country name!!
    def get_season(self, country: str, current_date: date):
        """Get the season in the given country on the given date."""
        month = current_date.month

        # FIX: Does this method need to catch exceptions because of this? How?
        location_zone = self.locate_country_zone(country)

        if location_zone == "Equator":
            ...
        else:
            # FIX: Unnecessairy check?
            hemispheres = self.season_hemisphere_mapping.get(month)
            if not hemispheres:
                raise ValueError(f"Provided {month} does not exist")

            season = hemispheres.get(location_zone)
            if not season:
                raise ValueError(f"No found season for location zone {location_zone}.")

        return season

    def locate_country_zone(self, country_name: str) -> str:
        """Identify the hemisphere in which the country is located or determine if it is situated on the equator."""

        # FIX correct error handling?
        # - can't connect to server
        with contextlib.suppress(geocoder.RequestException):
            location = geocoder.osm(country_name)

        # try:
        #     location = geocoder.osm(country_name)
        # except geocoder.RequestException as e:
        #     print(f"Request Exception: {e}")

        # Get the latitude from the location (country) given.
        latitude = location.latlng[0]

        if 0 < latitude <= 90:
            hemisphere = "Northern"
        elif -90 <= latitude < 0:
            hemisphere = "Southern"
        elif latitude == 0:
            hemisphere = "Equator"
        else:
            raise ValueError(f"No result found for the latitude {latitude}.")

        return hemisphere

    ##############################

    def get_current_season(self, current_date: date):  # noqa: D103
        """Get current season."""
        current_month = current_date.month

        if current_month in [12, 1, 2]:
            return "winter"
        if current_month in [3, 4, 5]:
            return "spring"
        if current_month in [6, 7, 8]:
            return "summer"
        if current_month in [9, 10, 11]:
            return "fall"

        return "winter"

    def get_current_holiday(self, hass: HomeAssistant):
        """Check if current date is in holiday range, then return current holiday."""
        current_date = dt_util.now().date()

        # Get holiday attributes
        # states = hass.states._states
        calendar_holiday_state = None
        start_time_next_holiday = None
        holiday_title = " "
        end_time_holiday = ""

        # translator = Translator()

        # loop all calendars and check if it is a holiday calendar
        # for state in states:
        #     if state.startswith("calendar"):
        #         holiday_string = state.split(".")[1]
        #         translation = translator.translate(holiday_string, dest="en")
        #         if "holiday" in translation.text.lower():
        #             # get the next holiday of this calendar
        #             calendar_holiday_state = hass.states.get(state)
        #             holiday = calendar_holiday_state.as_compressed_state["a"]
        #             start_time_this_holiday = holiday["start_time"]

        #             # if no calendar has been iterated previously, this calendar holiday info is saved
        #             if start_time_next_holiday is None:
        #                 start_time_next_holiday = start_time_this_holiday
        #                 end_time_holiday = holiday["end_time"]
        #                 holiday_title = holiday["message"]
        #             else:
        #                 # make the dates comparable
        #                 datetime_next_holiday = datetime.strptime(
        #                     start_time_next_holiday, "%Y-%m-%d %H:%M:%S"
        #                 )
        #                 datetime_this_holiday = datetime.strptime(
        #                     start_time_this_holiday, "%Y-%m-%d %H:%M:%S"
        #                 )

        #                 # saves the next holiday info of this calendar if the next holiday of this calendar is sooner than the previous calendar's next holiday
        #                 if datetime_this_holiday < datetime_next_holiday:
        #                     start_time_next_holiday = start_time_this_holiday
        #                     end_time_holiday = holiday["end_time"]
        #                     holiday_title = holiday["message"]

        if calendar_holiday_state is None:
            return "No holiday"

        week_before_holiday = start_time_next_holiday.date() - timedelta(weeks=1)

        # Check if current date is in holiday range
        if week_before_holiday <= current_date <= end_time_holiday.date():
            return holiday_title

        return "No holiday"

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

    def search_string_date(self, hass: HomeAssistant):
        """Generate a search string for the date feature, if there is no holiday, the current season, month and day is returned, otherwise the current holiday."""
        current_date = dt_util.now().date()

        if self.get_current_holiday(hass) == "No holiday":
            return f"{self.get_current_season(current_date)}, {self.get_month(current_date)}, {self.get_day_of_week(current_date)}"

        return f"{self.get_current_holiday(hass)}"
