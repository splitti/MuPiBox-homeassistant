"""Unified media player entity for MuPiBox-NG."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaClass,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import MuPiBoxConfigEntry
from .entity import MuPiBoxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the single logical MuPiBox media player."""
    async_add_entities([MuPiBoxMediaPlayer(entry)])


class MuPiBoxMediaPlayer(MuPiBoxEntity, MediaPlayerEntity):
    """Expose the box as one player independent of the active provider."""

    _attr_name = "Player"
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_media_image_remotely_accessible = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.BROWSE_MEDIA
    )

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        # Keep the existing local_player unique-id suffix so existing dashboards
        # and automations retain their entity registry entry after the merge.
        super().__init__(entry, "local_player")

    @property
    def _status(self) -> dict[str, Any]:
        return self.coordinator.data.status

    @property
    def _spotify(self) -> dict[str, Any]:
        return self.coordinator.data.spotify

    @property
    def _spotify_active(self) -> bool:
        data = self._spotify
        return bool(
            data.get("connected")
            and (data.get("playing") or data.get("paused") or data.get("buffering"))
        )

    def _current_track(self) -> dict[str, Any] | None:
        queue = self._status.get("queue")
        index = self._status.get("index", -1)
        if not isinstance(queue, list) or not isinstance(index, int):
            return None
        if index < 0 or index >= len(queue):
            return None
        track = queue[index]
        return track if isinstance(track, dict) else None

    @property
    def state(self) -> MediaPlayerState:
        if self._spotify_active:
            if self._spotify.get("buffering"):
                return MediaPlayerState.BUFFERING
            if self._spotify.get("playing"):
                return MediaPlayerState.PLAYING
            if self._spotify.get("paused"):
                return MediaPlayerState.PAUSED
            return MediaPlayerState.IDLE
        return {
            "playing": MediaPlayerState.PLAYING,
            "paused": MediaPlayerState.PAUSED,
            "stopped": MediaPlayerState.IDLE,
            "error": MediaPlayerState.IDLE,
        }.get(str(self._status.get("state", "")), MediaPlayerState.IDLE)

    @property
    def media_title(self) -> str | None:
        if self._spotify_active:
            track = self._spotify.get("track")
            return str(track.get("name")) if isinstance(track, dict) and track.get("name") else None
        track = self._current_track()
        return str(track.get("title")) if track and track.get("title") else None

    @property
    def media_artist(self) -> str | None:
        if self._spotify_active:
            track = self._spotify.get("track")
            artists = track.get("artists") if isinstance(track, dict) else None
            if isinstance(artists, list):
                return ", ".join(str(item) for item in artists)
            return None
        track = self._current_track()
        if not track:
            return None
        value = track.get("artist") or track.get("subtitle")
        return str(value) if value else None

    @property
    def media_album_name(self) -> str | None:
        if self._spotify_active:
            track = self._spotify.get("track")
            return str(track.get("album")) if isinstance(track, dict) and track.get("album") else None
        folder = self._status.get("folder")
        return str(folder) if folder else None

    @property
    def media_content_id(self) -> str | None:
        if self._spotify_active:
            track = self._spotify.get("track")
            return str(track.get("uri")) if isinstance(track, dict) and track.get("uri") else None
        track = self._current_track()
        return str(track.get("id")) if track and track.get("id") else None

    @property
    def media_content_type(self) -> str:
        return MediaType.MUSIC

    @property
    def media_duration(self) -> float | None:
        if self._spotify_active:
            track = self._spotify.get("track")
            value = track.get("duration_ms") if isinstance(track, dict) else None
            return float(value) / 1000 if isinstance(value, (int, float)) and value > 0 else None
        value = self._status.get("duration")
        return float(value) if isinstance(value, (int, float)) and value > 0 else None

    @property
    def media_position(self) -> float | None:
        if self._spotify_active:
            track = self._spotify.get("track")
            value = track.get("position_ms") if isinstance(track, dict) else None
            return float(value) / 1000 if isinstance(value, (int, float)) and value >= 0 else None
        value = self._status.get("position")
        return float(value) if isinstance(value, (int, float)) and value >= 0 else None

    @property
    def media_position_updated_at(self):
        if self.state is MediaPlayerState.PLAYING:
            return dt_util.utcnow()
        return None

    @property
    def media_image_url(self) -> str | None:
        if self._spotify_active:
            track = self._spotify.get("track")
            if isinstance(track, dict) and track.get("cover"):
                return str(track["cover"])
            return None
        return self.api.absolute_url(self._status.get("cover"))

    @property
    def volume_level(self) -> float | None:
        # MuPiBox-NG synchronizes all playback backends to one box volume.
        volume = self._status.get("volume")
        maximum = self._status.get("max_volume")
        if isinstance(volume, (int, float)) and isinstance(maximum, (int, float)) and maximum > 0:
            return max(0.0, min(1.0, float(volume) / float(maximum)))
        if self._spotify_active:
            volume = self._spotify.get("volume")
            maximum = self._spotify.get("volume_steps")
            if isinstance(volume, (int, float)) and isinstance(maximum, (int, float)) and maximum > 0:
                return max(0.0, min(1.0, float(volume) / float(maximum)))
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        provider = "spotify" if self._spotify_active else "local"
        if provider == "local":
            track = self._current_track()
            if track and track.get("provider"):
                provider = str(track["provider"])
        return {
            "active_provider": provider,
            "spotify_connected": bool(self._spotify.get("connected")),
        }

    async def _refresh(self) -> None:
        await self.coordinator.async_request_refresh()

    async def _local_command(self, action: str, **kwargs: Any) -> None:
        await self.api.async_command(action, **kwargs)
        await self._refresh()

    async def _spotify_command(self, action: str, value: int | None = None) -> None:
        await self.api.async_spotify_command(action, value)
        await self._refresh()

    async def async_media_play(self) -> None:
        if self._spotify_active:
            await self._spotify_command("resume")
        else:
            await self._local_command("play")

    async def async_media_pause(self) -> None:
        if self._spotify_active:
            await self._spotify_command("pause")
        else:
            await self._local_command("pause")

    async def async_media_stop(self) -> None:
        if self._spotify_active:
            await self._spotify_command("pause")
        else:
            await self._local_command("stop")

    async def async_media_next_track(self) -> None:
        if self._spotify_active:
            await self._spotify_command("next")
        else:
            await self._local_command("next")

    async def async_media_previous_track(self) -> None:
        if self._spotify_active:
            await self._spotify_command("previous")
        else:
            await self._local_command("previous")

    async def async_media_seek(self, position: float) -> None:
        if self._spotify_active:
            await self._spotify_command("seek", round(max(0.0, position) * 1000))
        else:
            await self._local_command("seek", value=float(position))

    async def async_set_volume_level(self, volume: float) -> None:
        maximum = self._status.get("max_volume")
        if not isinstance(maximum, (int, float)) or maximum <= 0:
            maximum = 100
        value = round(max(0.0, min(1.0, volume)) * float(maximum))
        if self._spotify_active:
            await self._spotify_command("volume", value)
        else:
            await self._local_command("volume", value=value)

    def _find_folder(self, folder_id: str) -> dict[str, Any] | None:
        for folder in self.coordinator.data.library:
            if str(folder.get("id")) == folder_id:
                return folder
        return None

    async def async_play_media(
        self,
        media_type: str,
        media_id: str,
        **kwargs: Any,
    ) -> None:
        del media_type, kwargs
        if media_id.startswith("spotify:"):
            await self.api.async_spotify_command("play", uri=media_id)
            await self._refresh()
            return
        if media_id.startswith("folder:"):
            await self._local_command("folder", folder_id=media_id.removeprefix("folder:"))
            return
        if media_id.startswith("track:"):
            body = media_id.removeprefix("track:")
            try:
                folder_id, index_text = body.rsplit(":", 1)
                index = int(index_text)
            except (ValueError, TypeError) as err:
                raise HomeAssistantError("Invalid MuPiBox track identifier") from err
            await self._local_command("resume", folder_id=folder_id, item_index=index)
            return
        if self._find_folder(media_id):
            await self._local_command("folder", folder_id=media_id)
            return
        raise HomeAssistantError(f"Unknown MuPiBox media id: {media_id}")

    async def async_browse_media(
        self,
        media_content_type: str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        del media_content_type
        if media_content_id in (None, "", "root"):
            children = []
            for folder in self.coordinator.data.library:
                folder_id = str(folder.get("id", ""))
                if not folder_id:
                    continue
                children.append(
                    BrowseMedia(
                        media_class=MediaClass.ALBUM,
                        media_content_id=f"folder:{folder_id}",
                        media_content_type=MediaType.MUSIC,
                        title=str(folder.get("name") or folder.get("relative") or folder_id),
                        can_play=True,
                        can_expand=True,
                        thumbnail=self.api.absolute_url(folder.get("cover")),
                    )
                )
            return BrowseMedia(
                media_class=MediaClass.DIRECTORY,
                media_content_id="root",
                media_content_type=MediaType.MUSIC,
                title="MuPiBox library",
                can_play=False,
                can_expand=True,
                children=children,
            )

        if media_content_id.startswith("folder:"):
            folder_id = media_content_id.removeprefix("folder:")
            folder = self._find_folder(folder_id)
            if folder is None:
                raise HomeAssistantError("MuPiBox folder is no longer available")
            tracks = folder.get("tracks") or []
            children = [
                BrowseMedia(
                    media_class=MediaClass.TRACK,
                    media_content_id=f"track:{folder_id}:{index}",
                    media_content_type=MediaType.MUSIC,
                    title=str(track.get("title") or f"Track {index + 1}"),
                    can_play=True,
                    can_expand=False,
                    thumbnail=self.api.absolute_url(folder.get("cover")),
                )
                for index, track in enumerate(tracks)
                if isinstance(track, dict)
            ]
            return BrowseMedia(
                media_class=MediaClass.ALBUM,
                media_content_id=media_content_id,
                media_content_type=MediaType.MUSIC,
                title=str(folder.get("name") or folder_id),
                can_play=True,
                can_expand=True,
                children=children,
                thumbnail=self.api.absolute_url(folder.get("cover")),
            )

        raise HomeAssistantError(f"Unknown MuPiBox browse id: {media_content_id}")
