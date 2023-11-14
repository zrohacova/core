from homeassistant.components.spotify.recommendation_handling import (
    RecommendationHandler,
)
from unittest.mock import patch

def test_api_call():
  with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
    _recommendation_handler = RecommendationHandler()
    item = _recommendation_handler.handling_weather_recommendations(None, spotify_mock)
    assert item