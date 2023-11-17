"""Contains the WeatherPlaylistMapper class, which provides functionality to map weather conditions and temperature ranges to an appropriate search string to be entered in Spotify."""

import calendar  # noqa: D100
from datetime import date, timedelta
import json

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util


class WeatherPlaylistMapper:
    """A class to map weather conditions and temperatures to a matching search string for Spotify."""

    # Constant for the temperature threshold
    TEMPERATURE_THRESHOLD_CELSIUS = 15

    def __init__(self, mapping_file="spotify_mappings.json") -> None:
        """Initialize the WeatherPlaylistMapper with mappings from a file.

        Args:
            mapping_file (str): The path to the JSON file containing playlist mappings.

        Raises:
            FileNotFoundError: If the mapping file is not found.
        """
        try:
            with open(mapping_file, encoding="utf-8") as file:
                self.spotify_category_mapping = json.load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"The mapping file {mapping_file} was not found."
            ) from e

    def map_weather_to_playlists(self, temperature: float, condition: str) -> str:
        """Map the given weather condition and temperature to an appropriate search string in Spotify.

        Args:
            temperature (float): The current temperature.
            condition (str): The current weather condition.

        Returns:
            str: A Spotify search string corresponding to the given weather condition
                 and temperature.

        Raises:
            ValueError: If the condition is not recognized or no mapping exists for the
                        given temperature category.
        """

        # Normalize the condition to lower case for reliable matching
        condition = condition.strip().lower()

        # Determine if the temperature is warm or cold
        # FIX: Consider the unit of temperature (Fahrenheit or Celsius) and handle accordingly.
        temperature_category = (
            "cold" if temperature < self.TEMPERATURE_THRESHOLD_CELSIUS else "warm"
        )

        # Retrieve the suitable Spotify category ID from the mapping
        # Handle cases where the condition is not in the mapping
        # FIX: Handle the ValueError in the code that calls this method,
        condition_mapping = self.spotify_category_mapping.get(condition)
        if not condition_mapping:
            raise ValueError(f"Weather condition {condition} does not exist")

        spotify_search_string = condition_mapping.get(temperature_category)
        if not spotify_search_string:
            raise ValueError(
                f"No playlist search string mapping for temperature category: {temperature_category}"
            )

        return spotify_search_string


class HolidaySeasonMapper:
    """A class to find the current holiday for a certain country and date, or season if there is no holiday."""

    # Based on the classifications made in country_location_mappings, which specifies if a country is located on the
    # northern or southern hemisphere, or on the equator. These countries all have similar seasons.

    def __init__(self, mapping_file="country_location_mappings.json") -> None:
        """Initialize the HolidaySeasonMapper with mappings from a file.

        Args:
            mapping_file (str): The path to the JSON file containing countries and their geographical location, specifying whether they are in the Northern Hemisphere, Southern Hemisphere, or on the equator.

        Raises:
            FileNotFoundError: If the mapping file is not found.
        """

        try:
            with open(mapping_file, encoding="utf-8") as file:
                self.country_location_mapping = json.load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"The mapping file {mapping_file} was not found."
            ) from e

    # FIX: what is the type for the date provided? Will we need to check that it has the correct form?
    def get_holiday_or_season(self, country: str, date_param: date):
        """Get the holiday in the country for the specified date. If there is no holiday in the given country on that date, the season is retrieved.

        Args:
            country (str): The country to find the holiday or season for.
            date_param (FIX): The current date.

        Returns:
            str: The holiday for the given date in the given country, or the season based on the date and country if there is no holiday.

        Raises:
            FIX
        """

        # Find the season in the country at given date
        geo_location = self.country_location_mapping.get(country)
        season = self.get_season(geo_location, date_param)

        return season

    def get_season(self, geo_location: str, date_param: date):
        """Get the season in the given country on the given date."""
        month = date_param.month

        if month in [1, 2, 12]:
            if geo_location == "Northern":
                season = "Winter"
            else:
                season = "Summer"
        elif month in [3, 4, 5]:
            if geo_location == "Northern":
                season = "Spring"
            else:
                season = "Autumn"
        elif month in [6, 7, 8]:
            if geo_location == "Northern":
                season = "Summer"
            else:
                season = "Winter"
        elif month in [9, 10, 11]:
            if geo_location == "Northern":
                season = "Autumn"
            else:
                season = "Spring"

        if geo_location == "Equator":
            # FIX: Case of the equator. There are dry and wet seasons, but otherwise not the classical seasons of winter, spring, summer, and autumn. This needs to be discussed how we should do.
            ...

        return season

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

        calendar_holiday_state = hass.states.get("calendar.holidays_in_sweden")

        if calendar_holiday_state is None:
            return "No holiday"

        holiday = calendar_holiday_state.attributes
        start_time_holiday = holiday["start_time"]
        end_time_holiday = holiday["end_time"]
        holiday_title = holiday["message"]

        week_before_holiday = start_time_holiday.date() - timedelta(weeks=1)

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
