"""Module that groups code required to handle state restore for component."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

from homeassistant.const import (
    ATTR_SUPPORTED_FEATURES,
    SERVICE_MEDIA_PAUSE,
    SERVICE_MEDIA_PLAY,
    SERVICE_MEDIA_STOP,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_SET,
    STATE_BUFFERING,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.core import Context, HomeAssistant, State

from .const import (
    ATTR_INPUT_SOURCE,
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    ATTR_SOUND_MODE,
    DOMAIN,
    SERVICE_PLAY_MEDIA,
    SERVICE_SELECT_SOUND_MODE,
    SERVICE_SELECT_SOURCE,
    MediaPlayerEntityFeature,
)


async def call_service(
    service: str,
    keys: Iterable[str],
    hass: HomeAssistant,
    state: State,
    context: Context | None = None,
) -> None:
    """Call service with set of attributes given."""
    data = {"entity_id": state.entity_id}
    for key in keys:
        if key in state.attributes:
            data[key] = state.attributes[key]

    await hass.services.async_call(
        DOMAIN, service, data, blocking=True, context=context
    )


async def set_source_and_sound_mode(  # noqa: D103
    hass: HomeAssistant, state: State, features: int, context: Context | None = None
) -> None:
    if (
        ATTR_INPUT_SOURCE in state.attributes
        and features & MediaPlayerEntityFeature.SELECT_SOURCE
    ):
        await call_service(
            SERVICE_SELECT_SOURCE, [ATTR_INPUT_SOURCE], hass, state, context
        )

    if (
        ATTR_SOUND_MODE in state.attributes
        and features & MediaPlayerEntityFeature.SELECT_SOUND_MODE
    ):
        await call_service(
            SERVICE_SELECT_SOUND_MODE, [ATTR_SOUND_MODE], hass, state, context
        )

    if (
        ATTR_MEDIA_VOLUME_LEVEL in state.attributes
        and features & MediaPlayerEntityFeature.VOLUME_SET
    ):
        await call_service(
            SERVICE_VOLUME_SET, [ATTR_MEDIA_VOLUME_LEVEL], hass, state, context
        )

    if (
        ATTR_MEDIA_VOLUME_MUTED in state.attributes
        and features & MediaPlayerEntityFeature.VOLUME_MUTE
    ):
        await call_service(
            SERVICE_VOLUME_MUTE, [ATTR_MEDIA_VOLUME_MUTED], hass, state, context
        )


async def _async_reproduce_states(
    hass: HomeAssistant,
    state: State,
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce component states."""
    cur_state = hass.states.get(state.entity_id)
    features = cur_state.attributes[ATTR_SUPPORTED_FEATURES] if cur_state else 0

    if state.state == STATE_OFF and (features & MediaPlayerEntityFeature.TURN_OFF):
        await call_service(SERVICE_TURN_OFF, [], hass, state, context)
        # entities that are off have no other attributes to restore
        return

    if (
        state.state
        in (
            STATE_BUFFERING,
            STATE_IDLE,
            STATE_ON,
            STATE_PAUSED,
            STATE_PLAYING,
        )
        and features & MediaPlayerEntityFeature.TURN_ON
    ):
        await call_service(SERVICE_TURN_ON, [], hass, state, context)

    cur_state = hass.states.get(state.entity_id)
    features = cur_state.attributes[ATTR_SUPPORTED_FEATURES] if cur_state else 0

    # First set source & sound mode to match the saved supported features
    await set_source_and_sound_mode(hass, state, features, context)

    already_playing = (ATTR_MEDIA_CONTENT_TYPE in state.attributes) and (
        ATTR_MEDIA_CONTENT_ID in state.attributes
    )

    if already_playing and (features & MediaPlayerEntityFeature.PLAY_MEDIA):
        await call_service(
            SERVICE_PLAY_MEDIA,
            [ATTR_MEDIA_CONTENT_TYPE, ATTR_MEDIA_CONTENT_ID],
            hass,
            state,
            context,
        )

    if (
        not already_playing
        and state.state in (STATE_BUFFERING, STATE_PLAYING)
        and features & MediaPlayerEntityFeature.PLAY
    ):
        await call_service(SERVICE_MEDIA_PLAY, [], hass, state, context)
    elif state.state == STATE_IDLE and (features & MediaPlayerEntityFeature.STOP):
        await call_service(SERVICE_MEDIA_STOP, [], hass, state, context)
    elif state.state == STATE_PAUSED and (features & MediaPlayerEntityFeature.PAUSE):
        await call_service(SERVICE_MEDIA_PAUSE, [], hass, state, context)


async def async_reproduce_states(
    hass: HomeAssistant,
    states: Iterable[State],
    *,
    context: Context | None = None,
    reproduce_options: dict[str, Any] | None = None,
) -> None:
    """Reproduce component states."""
    await asyncio.gather(
        *(
            _async_reproduce_states(
                hass, state, context=context, reproduce_options=reproduce_options
            )
            for state in states
        )
    )
