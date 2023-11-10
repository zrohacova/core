from homeassistant.components.spotify.recommendation_handling import (
    RecommendationHandling,
)
from unittest.mock import patch

def test_api_call():
  with patch("homeassistant.components.spotify.config_flow.Spotify") as spotify_mock:
    _recommendation_handler = RecommendationHandling()
    item = _recommendation_handler.handling_weather_recommendatios(None, spotify_mock)
    assert item