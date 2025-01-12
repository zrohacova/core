"""DataUpdateCoordinator for the Yale integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from yalesmartalarmclient.client import YaleSmartAlarmClient
from yalesmartalarmclient.exceptions import AuthenticationError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER, YALE_BASE_ERRORS


class YaleDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """A Yale Data Update Coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the Yale hub."""
        self.entry = entry
        self.yale: YaleSmartAlarmClient | None = None
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            always_update=False,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Yale."""

        updates = await self.hass.async_add_executor_job(self.get_updates)

        locks: list[dict[str, Any]] = []
        door_windows: list[dict[str, Any]] = []

        device_status_lock = "device_status.lock"
        device_status_unlock = "device_status.unlock"
        device_status_close = "device_status.dc_close"
        device_status_open = "device_status.dc_open"

        for device in updates["cycle"]["device_status"]:
            state = device["status1"]
            if device["type"] == "device_type.door_lock":
                self.process_door_lock(
                    device, locks, device_status_lock, device_status_unlock, state
                )
            elif device["type"] == "device_type.door_contact":
                self.process_door_contact(
                    device, door_windows, device_status_close, device_status_open, state
                )

        _sensor_map = {
            contact["address"]: contact["_state"] for contact in door_windows
        }
        _lock_map = {lock["address"]: lock["_state"] for lock in locks}

        return {
            "alarm": updates["arm_status"],
            "locks": locks,
            "door_windows": door_windows,
            "status": updates["status"],
            "online": updates["online"],
            "sensor_map": _sensor_map,
            "lock_map": _lock_map,
            "panel_info": updates["panel_info"],
        }

    def process_door_lock(
        self,
        device: dict[str, Any],
        locks: list[dict[str, Any]],
        device_status_lock: str,
        device_status_unlock: str,
        state: str,
    ) -> None:
        """Process the data for a door lock device."""

        lock_status_str = device["minigw_lock_status"]
        lock_status = int(str(lock_status_str or 0), 16)
        closed = (lock_status & 16) == 16
        locked = (lock_status & 1) == 1

        if not lock_status and device_status_lock in state:
            device["_state"] = "locked"
            device["_state2"] = "unknown"

        elif not lock_status and device_status_unlock in state:
            device["_state"] = "unlocked"
            device["_state2"] = "unknown"

        elif (
            lock_status
            and (device_status_lock in state or device_status_unlock in state)
            and closed
            and locked
        ):
            device["_state"] = "locked"
            device["_state2"] = "closed"

        elif (
            lock_status
            and (device_status_lock in state or device_status_unlock in state)
            and closed
            and not locked
        ):
            device["_state"] = "unlocked"
            device["_state2"] = "closed"

        elif (
            lock_status
            and (device_status_lock in state or device_status_unlock in state)
            and not closed
        ):
            device["_state"] = "unlocked"
            device["_state2"] = "open"
        else:
            device["_state"] = "unavailable"

        locks.append(device)

    def process_door_contact(
        self,
        device: dict[str, Any],
        door_windows: list[dict[str, Any]],
        device_status_close: str,
        device_status_open: str,
        state: str,
    ) -> None:
        """Process the data for a door contact device."""

        if device_status_close in state:
            device["_state"] = "closed"

        elif device_status_open in state:
            device["_state"] = "open"

        else:
            device["_state"] = "unavailable"

        door_windows.append(device)

    def get_updates(self) -> dict[str, Any]:
        """Fetch data from Yale."""

        if self.yale is None:
            try:
                self.yale = YaleSmartAlarmClient(
                    self.entry.data[CONF_USERNAME], self.entry.data[CONF_PASSWORD]
                )
            except AuthenticationError as error:
                raise ConfigEntryAuthFailed from error
            except YALE_BASE_ERRORS as error:
                raise UpdateFailed from error

        try:
            arm_status = self.yale.get_armed_status()
            data = self.yale.get_all()
            cycle = data["CYCLE"]
            status = data["STATUS"]
            online = data["ONLINE"]
            panel_info = data["PANEL INFO"]

        except AuthenticationError as error:
            raise ConfigEntryAuthFailed from error
        except YALE_BASE_ERRORS as error:
            raise UpdateFailed from error

        return {
            "arm_status": arm_status,
            "cycle": cycle,
            "status": status,
            "online": online,
            "panel_info": panel_info,
        }
