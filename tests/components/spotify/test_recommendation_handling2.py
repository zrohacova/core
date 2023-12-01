"""Test Spotify Recommendation Handler."""

from unittest.mock import patch

from homeassistant.components.spotify.recommendation_handling import (
    RecommendationHandler,
)
from homeassistant.core import HomeAssistant

from tests.components.accuweather import init_integration


async def test_handling_weather_recommendations(hass: HomeAssistant) -> None:
    """Test handling weather recommendations."""
    handler = RecommendationHandler()
    await init_integration(hass)

    with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
        spotify_mock.search.return_value = {
            "playlists": {
                "items": [
                    {"name": "Sunny Day Playlist 1", "id": "playlist_id_1"},
                    {"name": "Sunny Day Playlist 2", "id": "playlist_id_2"},
                ]
            }
        }

        media, items = handler.handling_weather_recommendations(hass, spotify_mock)

        assert items
        assert media

        assert len(items) == 2

        # assert handler._last_weather_search_string == "Sunny Day"
        # assert items == handler._last_api_call_result_weather
        # spotify_mock.search.assert_called_once_with(
        #     q="Sunny Day", type="playlist", limit=48
        # )


# class TestRecommendationHandler(unittest.TestCase):
#     """Test class for the RecommendationHandler class."""

#     def setUp(self):
#         """Set up the test environment."""
#         self.hass = MagicMock()
#         self.spotify = MagicMock()
#         self.handler = RecommendationHandler()

#     @patch(
#         "builtins.open",
#         new_callable=unittest.mock.mock_open,
#         read_data='{"sunny": {"warm": "Sunny Day"}}',
#     )
#     def test_handling_weather_recommendations(self, mock_open):
#         """Test handling weather recommendations.

#         This test checks whether the `handling_weather_recommendations` method
#         of the RecommendationHandler class behaves as expected.
#         """
#         weather_state = MagicMock()
#         weather_state.attributes = {
#             "temperature": 20,
#             "forecast": [{"condition": "sunny"}],
#         }
#         self.hass.states.get.return_value = weather_state

#         # Mocking Spotify search result
#         self.spotify.search.return_value = {
#             "playlists": {
#                 "items": [
#                     {"name": "Sunny Day Playlist 1", "id": "playlist_id_1"},
#                     {"name": "Sunny Day Playlist 2", "id": "playlist_id_2"},
#                 ]
#             }
#         }

#         # Call the method
#         with patch("os.path.isfile", return_value=True):
#             media, items = self.handler.handling_weather_recommendations(
#                 self.hass, self.spotify
#             )

#         # Assertions
#         self.assertEqual(self.handler._last_weather_search_string, "Sunny Day")
#         self.assertEqual(items, self.handler._last_api_call_result_weather)
#         self.assertEqual(media, self.handler._media)
#         self.spotify.search.assert_called_once_with(
#             q="Sunny Day", type="playlist", limit=48
#         )


# if __name__ == "__main__":
#     unittest.main()
