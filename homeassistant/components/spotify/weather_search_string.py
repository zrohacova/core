"""Contains the WeatherPlaylistMapper class, which provides functionality to map weather conditions and temperature ranges to an appropriate search string to be entered in Spotify."""
import json


class WeatherPlaylistMapper:
    """A class to map weather conditions and temperatures to a matching search string for Spotify."""

    # Constant for the temperature threshold
    TEMPERATURE_THRESHOLD_CELSIUS = 15
    TEMPERATURE_THRESHOLD_FAHRENHEIT = 59

    def __init__(
        self, mapping_file="homeassistant/components/spotify/spotify_mappings.json"
    ) -> None:
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

    def map_weather_to_playlists(
        self, temperature: float, condition: str, temperature_unit: str
    ) -> str:
        """Map the given weather condition and temperature to an appropriate search string in Spotify.

        Args:
            temperature (float): The current temperature.
            condition (str): The current weather condition.
            temperature_unit (str): The unit of temperature, either 'celsius' or 'fahrenheit'

        Returns:
            str: A Spotify search string corresponding to the given weather condition
                 and temperature.

        Raises:
            ValueError: If the condition is not recognized or no mapping exists for the
                        given temperature category.
        """

        # Normalize the condition to lower case for reliable matching
        condition = condition.strip().lower()

        temperature_threshold = (
            self.TEMPERATURE_THRESHOLD_CELSIUS
            if temperature_unit == "celsius"
            else self.TEMPERATURE_THRESHOLD_FAHRENHEIT
        )

        temperature_category = "cold" if temperature < temperature_threshold else "warm"

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
