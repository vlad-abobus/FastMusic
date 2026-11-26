from __future__ import annotations

import os
import time
from typing import Optional

import deezer
from dotenv import load_dotenv

from logger import get_logger

load_dotenv()

log = get_logger(__name__)


class DeezerClient:
    def __init__(self, token: Optional[str] = None):
        token = token or os.getenv("DEEZER_TOKEN")
        self.client = deezer.Client(access_token=token) if token else deezer.Client()
        self._last_call = 0.0
        log.info("DeezerClient инициализирован (token=%s)", "есть" if token else "нет")

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < 0.2:
            time.sleep(0.2 - elapsed)
        self._last_call = time.time()

    # ---- Search ----

    def search_all(self, query: str, limit: int = 25) -> list[dict]:
        self._throttle()
        log.info("search_all: query='%s' limit=%d", query, limit)
        try:
            results = self.client.search(query)
            items = []
            for item in results:
                d = self._item_to_dict(item)
                if d:
                    items.append(d)
                    if len(items) >= limit:
                        break
            log.info("search_all: найдено %d результатов", len(items))
            return items
        except Exception as e:
            log.error("search_all error: %s", e, exc_info=True)
            return []

    def search_tracks(self, query: str, limit: int = 25) -> list[dict]:
        self._throttle()
        log.info("search_tracks: query='%s' limit=%d", query, limit)
        try:
            results = self.client.search(query)
            tracks = []
            for item in results:
                if isinstance(item, deezer.Track):
                    tracks.append(self._track_to_dict(item))
                    if len(tracks) >= limit:
                        break
            log.info("search_tracks: найдено %d треков", len(tracks))
            return tracks
        except Exception as e:
            log.error("search_tracks error: %s", e, exc_info=True)
            return []

    def search_albums(self, query: str, limit: int = 15) -> list[dict]:
        self._throttle()
        log.info("search_albums: query='%s' limit=%d", query, limit)
        try:
            results = self.client.search(query)
            albums = []
            for item in results:
                if isinstance(item, deezer.Album):
                    albums.append(self._album_to_dict(item))
                    if len(albums) >= limit:
                        break
            log.info("search_albums: найдено %d альбомов", len(albums))
            return albums
        except Exception as e:
            log.error("search_albums error: %s", e, exc_info=True)
            return []

    def search_artists(self, query: str, limit: int = 15) -> list[dict]:
        self._throttle()
        log.info("search_artists: query='%s' limit=%d", query, limit)
        try:
            results = self.client.search(query)
            artists = []
            for item in results:
                if isinstance(item, deezer.Artist):
                    artists.append(self._artist_to_dict(item))
                    if len(artists) >= limit:
                        break
            log.info("search_artists: найдено %d исполнителей", len(artists))
            return artists
        except Exception as e:
            log.error("search_artists error: %s", e, exc_info=True)
            return []

    # ---- Charts ----

    def get_charts(self, limit: int = 20) -> list[dict]:
        self._throttle()
        log.info("get_charts: limit=%d", limit)
        try:
            chart = self.client.get_chart(genre_id=0)
            tracks = []
            for i, track in enumerate(chart.tracks):
                if i >= limit:
                    break
                tracks.append(self._track_to_dict(track))
            log.info("get_charts: получено %d треков", len(tracks))
            return tracks
        except Exception as e:
            log.error("get_charts error: %s", e, exc_info=True)
            return []

    # ---- Recommendations ----

    def get_artist_top(self, artist_id: int, limit: int = 10) -> list[dict]:
        self._throttle()
        log.info("get_artist_top: artist_id=%d limit=%d", artist_id, limit)
        try:
            artist = self.client.get_artist(artist_id)
            tracks = []
            for i, track in enumerate(artist.get_top()):
                if i >= limit:
                    break
                tracks.append(self._track_to_dict(track))
            log.info("get_artist_top: artist_id=%d, получено %d треков", artist_id, len(tracks))
            return tracks
        except Exception as e:
            log.error("get_artist_top error (artist_id=%d): %s", artist_id, e, exc_info=True)
            return []

    def get_related_artists(self, artist_id: int, limit: int = 10) -> list[dict]:
        self._throttle()
        log.info("get_related_artists: artist_id=%d limit=%d", artist_id, limit)
        try:
            artist = self.client.get_artist(artist_id)
            artists = []
            for i, related in enumerate(artist.get_related()):
                if i >= limit:
                    break
                artists.append(self._artist_to_dict(related))
            log.info("get_related_artists: artist_id=%d, получено %d исполнителей", artist_id, len(artists))
            return artists
        except Exception as e:
            log.error("get_related_artists error (artist_id=%d): %s", artist_id, e, exc_info=True)
            return []

    # ---- Getters ----

    def get_track(self, track_id: int) -> Optional[dict]:
        self._throttle()
        log.info("get_track: track_id=%d", track_id)
        try:
            track = self.client.get_track(track_id)
            log.info("get_track: track_id=%d -> '%s'", track_id, track.title)
            return self._track_to_dict(track)
        except Exception as e:
            log.error("get_track error (track_id=%d): %s", track_id, e, exc_info=True)
            return None

    def get_album(self, album_id: int) -> Optional[dict]:
        self._throttle()
        log.info("get_album: album_id=%d", album_id)
        try:
            album = self.client.get_album(album_id)
            log.info("get_album: album_id=%d -> '%s'", album_id, album.title)
            return self._album_to_dict(album)
        except Exception as e:
            log.error("get_album error (album_id=%d): %s", album_id, e, exc_info=True)
            return None

    def get_artist(self, artist_id: int) -> Optional[dict]:
        self._throttle()
        log.info("get_artist: artist_id=%d", artist_id)
        try:
            artist = self.client.get_artist(artist_id)
            log.info("get_artist: artist_id=%d -> '%s'", artist_id, artist.name)
            return self._artist_to_dict(artist)
        except Exception as e:
            log.error("get_artist error (artist_id=%d): %s", artist_id, e, exc_info=True)
            return None

    # ---- Converters ----

    @staticmethod
    def _item_to_dict(item) -> Optional[dict]:
        if isinstance(item, deezer.Track):
            return DeezerClient._track_to_dict(item)
        elif isinstance(item, deezer.Album):
            return DeezerClient._album_to_dict(item)
        elif isinstance(item, deezer.Artist):
            return DeezerClient._artist_to_dict(item)
        return None

    @staticmethod
    def _track_to_dict(track) -> dict:
        artist = track.artist
        album = track.album
        return {
            'id': track.id,
            'title': track.title,
            '_type': 'track',
            'artist': {
                'name': artist.name,
                'id': artist.id,
            },
            'album': {
                'title': album.title if album else '',
                'cover_small': album.cover_small if album else '',
                'cover_medium': album.cover_medium if album else '',
            },
            'duration': track.duration,
            'preview': track.preview,
        }

    @staticmethod
    def _album_to_dict(album) -> dict:
        return {
            'id': album.id,
            'title': album.title,
            '_type': 'album',
            'artist': album.artist.name if album.artist else 'Unknown',
            'cover_medium': album.cover_medium,
            'cover_small': album.cover_small,
            'tracks_count': album.nb_tracks,
            'release_date': album.release_date,
        }

    @staticmethod
    def _artist_to_dict(artist) -> dict:
        return {
            'id': artist.id,
            'name': artist.name,
            '_type': 'artist',
            'picture_medium': artist.picture_medium,
            'picture_big': artist.picture_big,
            'nb_fans': artist.nb_fan,
            'nb_albums': artist.nb_album,
        }
