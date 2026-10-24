"""Venue geocoding from the address Qloo returned, and nothing else.

Qloo place results carry a street address but no coordinates; only geographic
interest cells do. A venue is therefore plotted only when OpenStreetMap's
Nominatim resolves its own returned address unambiguously inside the requested
city. Everything else is reported as not plotted, with the reason. A coordinate
is never guessed, and an address match is not proof that the business trades
there today.

Nominatim's usage policy applies: at most one request per second, an
identifying User-Agent, cached results, no bulk use. Successful and definitive
"nothing found" answers are cached on disk; transport failures are not.
``GEOCODING_ENABLED=false`` serves only what is already held.
"""
from __future__ import annotations

import json
import math
import os
import threading
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from .evidence_store import STORE_DIR

NOMINATIM = 'https://nominatim.openstreetmap.org/search'
SOURCE = 'OpenStreetMap Nominatim, geocoded from the address Qloo returned'
SOURCE_NAME = 'OpenStreetMap Nominatim, matched by the venue name Qloo returned'
MIN_INTERVAL = 1.1
AMBIGUITY_KM = 1.5

_lock = threading.Lock()
_last_call = 0.0


def enabled() -> bool:
    return os.getenv('GEOCODING_ENABLED', 'true').strip().lower() not in ('0', 'false', 'no', 'off')


def _user_agent() -> str:
    return os.getenv('GEOCODING_USER_AGENT', 'CultureForge-AI/0.3 (+https://github.com/joyboyreturns/CultureForge-AI)')


def _cache_path() -> Path:
    return Path(os.getenv('CULTUREFORGE_GEOCODE_CACHE', STORE_DIR / 'geocode_cache.json'))


def _load() -> dict:
    try:
        return json.loads(_cache_path().read_text())
    except (OSError, ValueError):
        return {}


def _save(cache: dict) -> None:
    try:
        path = _cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache))
    except OSError:
        pass


def seed(entries: dict) -> int:
    """Add shipped, verified geocodes that are not held yet. Only definitive answers are accepted."""
    cache = _load()
    added = 0
    for key, verdict in entries.items():
        if key not in cache and isinstance(verdict, dict) and verdict.get('status') in (
                'plotted', 'not_found', 'outside_city', 'area_only', 'ambiguous'):
            cache[key] = verdict
            added += 1
    if added:
        _save(cache)
    return added


def _key(address: str, city: str) -> str:
    return f'v3|{address.strip().casefold()}|{city.strip().casefold()}'


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180
    h = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def _fold(text: str) -> str:
    """Lower-case without accents, so "Tōkyō" and "Tokyo" name the same city."""
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))


def clean(address: str) -> str:
    """The address without building names in other scripts and floor markers, which geocoders cannot match."""
    text = re.sub(r'[^\x00-\x7f]+', ' ', address)
    text = re.sub(r'\b\d+f\b', ' ', text, flags=re.I)
    return re.sub(r'\s+', ' ', text).strip(' ,')


def _in_city(row: dict, city: str) -> bool:
    """The returned place must name the requested city (or its region) in its own address."""
    wanted = _fold(city.split(',')[0].strip())
    if not wanted:
        return False
    parts = row.get('address') or {}
    haystack = _fold(' '.join(str(v) for v in parts.values()) + ' ' + str(row.get('display_name', '')))
    return wanted in haystack


def judge(rows: list[dict], city: str) -> dict:
    """Pure decision over Nominatim rows: plotted, not_found, outside_city or ambiguous."""
    if not rows:
        return {'status': 'not_found', 'reason': 'The geocoder found no match for the returned address.'}
    first = rows[0]
    try:
        point = (float(first['lat']), float(first['lon']))
    except (KeyError, TypeError, ValueError):
        return {'status': 'not_found', 'reason': 'The geocoder returned no usable coordinates.'}
    if not _in_city(first, city):
        return {'status': 'outside_city',
                'reason': f'The address resolved outside the requested city ({city.split(",")[0].strip()}); not plotted.'}
    if int(first.get('place_rank') or 30) < 26:
        return {'status': 'area_only', 'reason': 'Only the neighbourhood or street was found, not this address; '
                                                  'not plotted as a venue.'}
    for other in rows[1:]:
        try:
            if _km(point, (float(other['lat']), float(other['lon']))) > AMBIGUITY_KM and _in_city(other, city):
                return {'status': 'ambiguous', 'reason': 'The address matches places more than 1.5 km apart; not plotted.'}
        except (KeyError, TypeError, ValueError):
            continue
    return {'status': 'plotted', 'lat': point[0], 'lon': point[1],
            'matched': first.get('display_name', '')[:240], 'source': SOURCE,
            'precision': 'address match, not a surveyed venue point'}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r'\w+', _fold(text)) if len(t) > 1}


def name_match(rows: list[dict], name: str, city: str) -> Optional[dict]:
    """A venue found by its own name: the returned name must share most of its words with Qloo's name,
    sit inside the requested city and be a point-level result. Two independent signals, or nothing."""
    wanted = _tokens(name)
    for row in rows:
        have = _tokens(str(row.get('name', '')))
        if not wanted or not have or not _in_city(row, city) or int(row.get('place_rank') or 30) < 26:
            continue
        shared = wanted & have
        # A one-word overlap is not a name match: "No.4" shares only "no" with anything called "No ...",
        # and a short name would otherwise be satisfied by any longer one that contains it. Two shared
        # words are required unless the two names are the same words.
        if len(shared) / min(len(wanted), len(have)) >= 0.6 and (len(shared) >= 2 or wanted == have):
            return {'status': 'plotted', 'lat': float(row['lat']), 'lon': float(row['lon']),
                    'matched': row.get('display_name', '')[:240], 'source': SOURCE_NAME,
                    'precision': 'matched by venue name inside the city; not a surveyed venue point'}
    return None


def _fetch(address: str) -> Optional[list[dict]]:
    """One throttled Nominatim request. None means transport failure (never cached)."""
    global _last_call
    with _lock:
        wait = MIN_INTERVAL - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
        try:
            query = urllib.parse.urlencode({'q': address, 'format': 'jsonv2', 'limit': 2, 'addressdetails': 1, 'accept-language': 'en'})
            request = urllib.request.Request(f'{NOMINATIM}?{query}', headers={'User-Agent': _user_agent()})
            with urllib.request.urlopen(request, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
        except (OSError, ValueError):
            return None
    return data if isinstance(data, list) else None


def geocode_venues(venues: list[dict]) -> list[dict]:
    """Each venue: {id, address, city}. Returns one result per venue, in order."""
    cache = _load()
    results, dirty = [], False
    for venue in venues:
        vid, address, city = venue['id'], (venue.get('address') or '').strip(), (venue.get('city') or '').strip()
        if not address:
            results.append({'id': vid, 'status': 'no_address', 'reason': 'Qloo returned no address for this venue.'})
            continue
        key = _key(address, city)
        if key in cache:
            results.append({'id': vid, **cache[key], 'cached': True})
            continue
        if not enabled():
            results.append({'id': vid, 'status': 'unavailable', 'reason': 'Geocoding is switched off on this server.'})
            continue
        rows = _fetch(address)
        simpler = clean(address)
        if rows is not None and not rows and simpler and simpler != address:
            rows = _fetch(simpler)
        if rows is None:
            results.append({'id': vid, 'status': 'unavailable', 'reason': 'The geocoder could not be reached; try again.'})
            continue
        verdict = judge(rows, city)
        name = (venue.get('name') or '').strip()
        if verdict['status'] in ('not_found', 'area_only') and name:
            by_name = _fetch(f'{name}, {city.split(",")[0].strip()}')
            found = name_match(by_name or [], name, city)
            if found:
                verdict = found
        cache[key] = verdict
        _save(cache)  # per venue, so an abandoned request still leaves its work held
        dirty = False
        results.append({'id': vid, **verdict, 'cached': False})
    if dirty:
        _save(cache)
    return results
