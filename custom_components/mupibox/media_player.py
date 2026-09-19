"""Media player entities for MuPiBox-NG."""

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
    """Set up MuPiBox media players."""
    async_add_entities(
        [
            MuPiBoxLocalMediaPlayer(entry),
            MuPiBoxSpotifyMediaPlayer(entry),
        ]
    )


class MuPiBoxLocalMediaPlayer(MuPiBoxEntity, MediaPlayerEntity):
    """The native/local MuPiBox player."""

    _attr_name = "Local Player"
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
        super().__init__(entry, "local_player")

    @property
    def _status(self) -> dict[str, Any]:
        return self.coordinator.data.status

    @property
    def state(self) -> MediaPlayerState:
        return {
            "playing": MediaPlayerState.PLAYING,
            "paused": MediaPlayerState.PAUSED,
            "stopped": MediaPlayerState.IDLE,
            "error": MediaPlayerState.IDLE,
        }.get(str(self._status.get("state", "")), MediaPlayerState.IDLE)

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
    def media_title(self) -> str | None:
        track = self._current_track()
        return str(track.get("title")) if track and track.get("title") else None

    @property
    def media_album_name(self) -> str | None:
        folder = self._status.get("folder")
        return str(folder) if folder else None

    @property
    def media_content_id(self) -> str | None:
        track = self._current_track()
        return str(track.get("id")) if track and track.get("id") else None

    @property
    def media_content_type(self) -> str:
        return MediaType.MUSIC

    @property
    def media_duration(self) -> float | None:
        value = self._status.get("duration")
        return float(value) if isinstance(value, (int, float)) and value > 0 else None

    @property
    def media_position(self) -> float | None:
        value = self._status.get("position")
        return float(value) if isinstance(value, (int, float)) and value >= 0 else None

    @property
    def media_position_updated_at(self):
        if self.state is MediaPlayerState.PLAYING:
            return dt_util.utcnow()
        return None

    @property
    def media_image_url(self) -> str | None:
        return self.api.absolute_url(self._status.get("cover"))

    @property
    def volume_level(self) -> float | None:
        volume = self._status.get("volume")
        maximum = self._status.get("max_volume")
        if not isinstance(volume, (int, float)) or not isinstance(maximum, (int, float)):
            return None
        if maximum <= 0:
            return 0.0
        return max(0.0, min(1.0, float(volume) / float(maximum)))

    async def _command(self, action: str, **kwargs: Any) -> None:
        await self.api.async_command(action, **kwargs)
        await self.coordinator.async_request_refresh()

    async def async_media_play(self) -> None:
        await self._command("play")

    async def async_media_pause(self) -> None:
        await self._command("pause")

    async def async_media_stop(self) -> None:
        await self._command("stop")

    async def async_media_next_track(self) -> None:
        await self._command("next")

    async def async_media_previous_track(self) -> None:
        await self._command("previous")

    async def async_media_seek(self, position: float) -> None:
        await self._command("seek", value=float(position))

    async def async_set_volume_level(self, volume: float) -> None:
        maximum = self._status.get("max_volume")
        if not isinstance(maximum, (int, float)) or maximum <= 0:
            maximum = 100
        value = round(max(0.0, min(1.0, volume)) * float(maximum))
        await self._command("volume", value=value)

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
        if media_id.startswith("folder:"):
            await self._command("folder", folder_id=media_id.removeprefix("folder:"))
            return
        if media_id.startswith("track:"):
            body = media_id.removeprefix("track:")
            try:
                folder_id, index_text = body.rsplit(":", 1)
                index = int(index_text)
            except (ValueError, TypeError) as err:
                raise HomeAssistantError("Invalid MuPiBox track identifier") from err
            await self._command("resume", folder_id=folder_id, item_index=index)
            return
        if self._find_folder(media_id):
            await self._command("folder", folder_id=media_id)
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


class MuPiBoxSpotifyMediaPlayer(MuPiBoxEntity, MediaPlayerEntity):
    """Spotify Connect session exposed by MuPiBox-NG."""

    _attr_name = "Spotify Connect"
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_media_image_remotely_accessible = True
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.VOLUME_SET
    )

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "spotify_connect")

    @property
    def _spotify(self) -> dict[str, Any]:
        return self.coordinator.data.spotify

    @property
    def state(self) -> MediaPlayerState:
        data = self._spotify
        if not data or not data.get("connected"):
            return MediaPlayerState.OFF
        if data.get("buffering"):
            return MediaPlayerState.BUFFERING
        if data.get("playing"):
            return MediaPlayerState.PLAYING
        if data.get("paused"):
            return MediaPlayerState.PAUSED
        return MediaPlayerState.IDLE

    @property
    def media_title(self) -> str | None:
        track = self._spotify.get("track")
        return str(track.get("name")) if isinstance(track, dict) and track.get("name") else None

    @property
    def media_artist(self) -> str | None:
        track = self._spotify.get("track")
        artists = track.get("artists") if isinstance(track, dict) else None
        if isinstance(artists, list):
            return ", ".join(str(item) for item in artists)
        return None

    @property
    def media_album_name(self) -> str | None:
        track = self._spotify.get("track")
        return str(track.get("album")) if isinstance(track, dict) and track.get("album") else None

    @property
    def media_content_type(self) -> str:
        return MediaType.MUSIC

    @property
    def media_duration(self) -> float | None:
        track = self._spotify.get("track")
        value = track.get("duration_ms") if isinstance(track, dict) else None
        return float(value) / 1000 if isinstance(value, (int, float)) and value > 0 else None

    @property
    def media_position(self) -> float | None:
        track = self._spotify.get("track")
        value = track.get("position_ms") if isinstance(track, dict) else None
        return float(value) / 1000 if isinstance(value, (int, float)) and value >= 0 else None

    @property
    def media_position_updated_at(self):
        if self.state is MediaPlayerState.PLAYING:
            return dt_util.utcnow()
        return None

    @property
    def media_image_url(self) -> str | None:
        track = self._spotify.get("track")
        if isinstance(track, dict) and track.get("cover"):
            return str(track["cover"])
        return None

    @property
    def volume_level(self) -> float | None:
        volume = self._spotify.get("volume")
        steps = self._spotify.get("volume_steps")
        if not isinstance(volume, (int, float)) or not isinstance(steps, (int, float)):
            return None
        if steps <= 0:
            return 0.0
        return max(0.0, min(1.0, float(volume) / float(steps)))

    async def _spotify_command(self, action: str, value: int | None = None) -> None:
        await self.api.async_spotify_command(action, value)
        await self.coordinator.async_request_refresh()

    async def async_media_play(self) -> None:
        await self._spotify_command("resume")

    async def async_media_pause(self) -> None:
        await self._spotify_command("pause")

    async def async_media_stop(self) -> None:
        await self._spotify_command("pause")

    async def async_media_next_track(self) -> None:
        await self._spotify_command("next")

    async def async_media_previous_track(self) -> None:
        await self._spotify_command("previous")

    async def async_media_seek(self, position: float) -> None:
        await self._spotify_command("seek", round(max(0.0, position) * 1000))

    async def async_set_volume_level(self, volume: float) -> None:
        steps = self._spotify.get("volume_steps")
        if not isinstance(steps, (int, float)) or steps <= 0:
            steps = 100
        await self._spotify_command(
            "volume", round(max(0.0, min(1.0, volume)) * float(steps))
        )
