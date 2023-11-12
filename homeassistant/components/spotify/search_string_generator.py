"""Contains the WeatherPlaylistMapper class, which provides functionality to map weather conditions and temperature ranges to corresponding Spotify playlist IDs."""

from datetime import date
import json


class WeatherPlaylistMapper:
    """A class to map weather conditions and temperatures to Spotify playlist categories."""

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
        """Map the given weather condition and temperature to a Spotify playlist category ID.

        Args:
            temperature (float): The current temperature.
            condition (str): The current weather condition.

        Returns:
            str: The Spotify playlist ID corresponding to the given weather condition
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
