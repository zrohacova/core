"""Contains the WeatherPlaylistMapper class, which provides functionality to map weather conditions and temperature ranges to corresponding Spotify playlist IDs."""

from datetime import date
import json

import country_converter as coco
import geocoder
import requests


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
            # FIX necessairy?
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
