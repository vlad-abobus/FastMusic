from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import pyradios
from logger import get_logger

log = get_logger(__name__)


@dataclass
class RadioStation:
    name: str
    url: str
    country: str = ""
    language: str = ""
    tags: str = ""
    codec: str = ""
    bitrate: int = 0
    favicon: str = ""
    station_uuid: str = ""
    votes: int = 0


class RadioBrowserClient:
    def __init__(self):
        self._client = pyradios.RadioBrowser()
        log.info("RadioBrowserClient инициализирован")

    def search_by_name(self, query: str, limit: int = 30) -> list[RadioStation]:
        try:
            log.info("Поиск радио по имени: '%s' limit=%d", query, limit)
            raw = self._client.stations_by_name(name=query, limit=limit, reverse=True)
            return self._parse_stations(raw)
        except Exception as e:
            log.error("Ошибка поиска радио по имени: %s", e, exc_info=True)
            return []

    def search_by_tag(self, tag: str, limit: int = 30) -> list[RadioStation]:
        try:
            log.info("Поиск радио по тегу: '%s' limit=%d", tag, limit)
            raw = self._client.stations_by_tag(tag=tag, limit=limit, reverse=True)
            return self._parse_stations(raw)
        except Exception as e:
            log.error("Ошибка поиска радио по тегу: %s", e, exc_info=True)
            return []

    def search_by_country(self, country: str, limit: int = 30) -> list[RadioStation]:
        try:
            log.info("Поиск радио по стране: '%s' limit=%d", country, limit)
            raw = self._client.stations_by_country(country=country, limit=limit, reverse=True)
            return self._parse_stations(raw)
        except Exception as e:
            log.error("Ошибка поиска радио по стране: %s", e, exc_info=True)
            return []

    def get_by_countrycode(self, code: str, limit: int = 30) -> list[RadioStation]:
        try:
            log.info("Радио по коду страны: '%s' limit=%d", code, limit)
            raw = self._client.stations_by_countrycode(countrycode=code, limit=limit, reverse=True)
            return self._parse_stations(raw)
        except Exception as e:
            log.error("Ошибка получения радио по коду страны: %s", e, exc_info=True)
            return []

    def get_popular(self, limit: int = 30) -> list[RadioStation]:
        try:
            log.info("Популярные радиостанции limit=%d", limit)
            raw = self._client.stations(order="votes", reverse=True, limit=limit)
            return self._parse_stations(raw)
        except Exception as e:
            log.error("Ошибка получения популярных радио: %s", e, exc_info=True)
            return []

    @staticmethod
    def _parse_stations(raw: list) -> list[RadioStation]:
        result = []
        for s in raw:
            try:
                url = s.get("url", "") or s.get("url_resolved", "")
                if not url:
                    continue
                result.append(RadioStation(
                    name=s.get("name", "Unknown").strip(),
                    url=url,
                    country=s.get("country", ""),
                    language=s.get("language", ""),
                    tags=s.get("tags", ""),
                    codec=s.get("codec", ""),
                    bitrate=s.get("bitrate", 0) or 0,
                    favicon=s.get("favicon", ""),
                    station_uuid=s.get("stationuuid", ""),
                    votes=s.get("votes", 0) or 0,
                ))
            except Exception:
                continue
        return result

    @staticmethod
    def is_valid_url(url: str) -> bool:
        if not url:
            return False
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https") and bool(parsed.netloc)
        except Exception:
            return False
