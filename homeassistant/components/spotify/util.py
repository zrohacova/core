"""Utils for Spotify."""
from __future__ import annotations

from typing import Any

import yarl

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import MEDIA_PLAYER_PREFIX


def is_spotify_media_type(media_content_type: str) -> bool:
    """Return whether the media_content_type is a valid Spotify media_id."""
    return media_content_type.startswith(MEDIA_PLAYER_PREFIX)


def resolve_spotify_media_type(media_content_type: str) -> str:
    """Return actual spotify media_content_type."""
    return media_content_type.removeprefix(MEDIA_PLAYER_PREFIX)


def fetch_image_url(item: dict[str, Any], key="images") -> str | None:
    """Fetch image url."""
    try:
        return item.get(key, [])[0].get("url")
    except IndexError:
        return None


def spotify_uri_from_media_browser_url(media_content_id: str) -> str:
    """Extract spotify URI from media browser URL."""
    if media_content_id and media_content_id.startswith(MEDIA_PLAYER_PREFIX):
        parsed_url = yarl.URL(media_content_id)
        media_content_id = parsed_url.name
    return media_content_id


def get_entity_ids(hass: HomeAssistant, domain: str) -> list[str]:
    """Retrieve entity id's for connected integrations in the given domain."""
    entity_reg = er.async_get(hass)
    return [
        entity.entity_id
        for entity in entity_reg.entities.values()
        if entity.domain == domain
    ]
