"""Business-category resolution, kept apart from the audience's interests.

A category is a business the founder wants to open. It is read from the idea's
own words, through a table of canonical categories with synonyms (several
languages) and the Qloo ``find_tags`` term that resolves its real taxonomy
identifier at run time. No tag URN is written here: identifiers come only from
a returned ``find_tags`` envelope.

A phrase that is not in the table is not rejected. Its head phrase becomes an
open-vocabulary query, so an unfamiliar business is still resolved against the
real taxonomy, and says that it was.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

#: id -> label, synonyms, the find_tags query, and the returned-text terms that
#: mark a place as that business. ``adjacent`` names categories whose places are
#: related businesses but not the one requested.
CATEGORIES: dict[str, dict] = {
    'frozen_dessert': {
        'label': 'Ice cream parlour',
        'terms': ('ice cream parlour', 'ice cream parlor', 'ice cream shop', 'ice cream', 'gelato', 'gelateria',
                  'frozen yogurt', 'frozen yoghurt', 'sorbet', 'creamery', 'glace', 'glacier', 'helado',
                  'heladeria', 'eis', 'eiscafe', 'eisdiele', 'アイスクリーム', '冰淇淋', '아이스크림'),
        'query': 'ice cream', 'adjacent': ('bakery', 'coffee')},
    'bakery': {
        'label': 'Bakery',
        'terms': ('bakery', 'bakeries', 'boulangerie', 'patisserie', 'pâtisserie', 'panaderia', 'panadería',
                  'baeckerei', 'bäckerei', 'bread shop', 'pastry shop', 'パン屋', 'ベーカリー', '빵집'),
        'query': 'bakery', 'adjacent': ('coffee', 'frozen_dessert')},
    'coffee': {
        'label': 'Coffee shop',
        'terms': ('specialty coffee shop', 'specialty coffee', 'coffee shop', 'coffee roaster', 'coffeehouse',
                  'espresso bar', 'coffee bar', 'cafe', 'café', 'coffee', 'kaffeehaus', 'カフェ', '咖啡', '카페'),
        'query': 'coffee shop', 'adjacent': ('bakery',)},
    'books': {
        'label': 'Bookstore',
        'terms': ('independent bookstore', 'bookstore', 'book store', 'bookshop', 'book shop', 'librairie',
                  'libreria', 'librería', 'buchhandlung', '書店', '本屋', '서점'),
        'query': 'bookstore', 'adjacent': ('coffee',)},
    'records': {
        'label': 'Record store',
        'terms': ('record store', 'record shop', 'vinyl shop', 'vinyl store', 'records', 'disquaire', 'レコード店'),
        'query': 'record store', 'adjacent': ('music',)},
    'pizza': {
        'label': 'Pizzeria',
        'terms': ('neapolitan pizza', 'pizza restaurant', 'pizza shop', 'pizza store', 'pizza place', 'pizza parlour',
                  'pizza parlor', 'pizzeria', 'pizzería', 'pizza', 'ピザ', '披萨', '피자'),
        'query': 'pizza', 'adjacent': ('restaurant',)},
    'restaurant': {
        'label': 'Restaurant',
        'terms': ('vegan restaurant', 'vegetarian restaurant', 'restaurant', 'bistro', 'eatery', 'trattoria',
                  'brasserie', 'ristorante', 'restaurante', 'レストラン', '餐厅', '식당'),
        'query': 'restaurant', 'adjacent': ('coffee', 'bakery')},
    'hotel': {
        'label': 'Boutique hotel',
        'terms': ('boutique hotel', 'hotel', 'guesthouse', 'guest house', 'ryokan', 'hostel', 'bed and breakfast',
                  'hôtel', 'ホテル', '旅館'),
        'query': 'boutique hotel', 'adjacent': ()},
    'fitness': {
        'label': 'Fitness studio',
        'terms': ('fitness studio', 'yoga studio', 'pilates studio', 'gym', 'fitness centre', 'fitness center',
                  'crossfit', 'boxing gym', 'ジム', '健身房', '헬스장'),
        'query': 'gym', 'adjacent': ('wellness',)},
    'wellness': {
        'label': 'Wellness / spa',
        'terms': ('wellness', 'spa', 'massage', 'sauna'),
        'query': 'spa', 'adjacent': ('fitness',)},
    'pet_cafe': {
        'label': 'Pet café',
        'terms': ('pet cafe', 'pet café', 'cat cafe', 'cat café', 'dog cafe', 'dog café', 'animal cafe',
                  '猫カフェ', '고양이 카페', '펫카페'),
        'query': 'pet cafe', 'adjacent': ('coffee',)},
    'florist': {
        'label': 'Flower shop',
        'terms': ('flower shop', 'flower store', 'florist', 'flowers', 'fleuriste', 'bloemist', 'blumenladen',
                  'floristeria', '花屋', '花店', '꽃집'),
        'query': 'florist', 'adjacent': ('gifts',)},
    'concept_store': {
        'label': 'Concept store',
        'terms': ('concept store', 'lifestyle store', 'select shop', 'design store', 'department store'),
        'query': 'concept store', 'adjacent': ('fashion', 'gifts')},
    'fashion': {
        'label': 'Fashion boutique',
        'terms': ('clothing boutique', 'fashion boutique', 'fashion store', 'clothing store', 'boutique', 'apparel',
                  'vintage clothing'),
        'query': 'clothing store', 'adjacent': ('concept_store',)},
    'gifts': {'label': 'Gift shop', 'terms': ('gift shop', 'gift store', 'souvenir shop'),
              'query': 'gift shop', 'adjacent': ()},
    'ceramics': {'label': 'Ceramics studio', 'terms': ('ceramics', 'ceramic', 'pottery', 'potter'),
                 'query': 'pottery', 'adjacent': ()},
    'music': {'label': 'Music venue', 'terms': ('music venue', 'live music', 'concert hall', 'jazz club'),
              'query': 'music venue', 'adjacent': ('records',)},
    'gaming': {'label': 'Gaming venue',
               'terms': ('gaming cafe', 'gaming bar', 'board game cafe', 'board game bar', 'internet cafe',
                         'esports bar', 'arcade', 'video game shop'),
               'query': 'arcade', 'adjacent': ()},
    'pharmacy': {'label': 'Pharmacy', 'terms': ('medical store', 'pharmacy', 'chemist', 'drugstore', 'apothecary'),
                 'query': 'pharmacy', 'adjacent': ()},
    'clinic': {'label': 'Clinic', 'terms': ('hospital', 'clinic', 'dentist'), 'query': 'clinic', 'adjacent': ()},
}

#: Places a founder may admire but that are not competitors of any retail or
#: food business. Matched as whole words in returned text.
ATTRACTION_TERMS = ('museum', 'gallery', 'monument', 'cathedral', 'palace', 'castle', 'memorial', 'landmark',
                    'opera', 'aquarium', 'zoo', 'botanical garden', 'national park', 'historic site', 'temple',
                    'shrine', 'church', 'exhibition', 'art centre', 'art center', 'cultural centre')

GENERIC_HEADS = frozenset({'cafe', 'café', 'coffee', 'restaurant', 'hotel', 'gym', 'boutique', 'flowers', 'records',
                           'wellness', 'spa', 'clinic', 'arcade', 'ceramics', 'bistro'})
NEUTRAL = frozenset({'a', 'an', 'the', 'best', 'good', 'great', 'new', 'small', 'local', 'independent', 'artisan',
                     'specialty', 'speciality', 'craft', 'modern', 'classic', 'boutique', 'neighbourhood',
                     'neighborhood', 'family', 'community', 'cozy', 'cosy', 'organic', 'vegan', 'vegetarian',
                     'sustainable', 'premium', 'luxury', 'third', 'wave', 'shop', 'store', 'studio', 'parlour',
                     'parlor', 'and', 'bar'})
GENERIC_ONLY = frozenset({'shop', 'store', 'studio', 'parlour', 'parlor', 'place', 'business', 'venue', 'bar',
                          'club', 'house', 'centre', 'center', 'space', 'company', 'startup'})

_FRAME = re.compile(
    r'^\s*(?:(?:where|how|what|which)\b[^?]*?\b(?:open|start|launch|build|set up|run)\s+)?'
    r'(?:(?:a|an|the|my|our|some)\s+)?', re.I)
_CUT = re.compile(r'\b(?:in|near|at|around|for|with|of|by|within)\b', re.I)


@dataclass(frozen=True)
class CategoryResolution:
    id: str                     # canonical id, '' when open-vocabulary or unresolved
    label: str
    query: str                  # the find_tags text; '' when unresolved
    status: str                 # canonical | open_vocabulary | unresolved
    matched: str = ''
    terms: tuple[str, ...] = ()
    adjacent: tuple[str, ...] = ()
    reason: str = ''
    alternatives: tuple[str, ...] = field(default_factory=tuple)


def head_phrase(idea: str) -> str:
    """The business noun phrase of an idea, without a question frame or place."""
    text = re.sub(r'[?.!]+$', '', (idea or '').strip())
    text = _FRAME.sub('', text, count=1)
    cut = _CUT.search(text)
    if cut and cut.start() > 0:
        text = text[:cut.start()]
    return re.sub(r'\s+', ' ', text).strip(' ,-')


def _contains(term: str, text: str) -> bool:
    if re.search(r'[^\x00-ɏ]', term):  # CJK and other scripts have no word boundaries
        return term in text
    return re.search(r'(?<![\w])' + re.escape(term) + r'(?![\w])', text) is not None


def resolve(idea: str) -> CategoryResolution:
    phrase = head_phrase(idea)
    text = (phrase or idea or '').casefold()
    if not text.strip():
        return CategoryResolution('', '', '', 'unresolved',
                                  reason='No business idea was given, so no category was resolved.')
    hits: list[tuple[int, str, str]] = []
    for cid, spec in CATEGORIES.items():
        for term in spec['terms']:
            if _contains(term.casefold(), text):
                hits.append((len(term), cid, term))
    if hits:
        top = max(length for length, _, _ in hits)
        best = sorted({(cid, term) for length, cid, term in hits if length == top})
        ids = {cid for cid, _ in best}
        if len(ids) > 1:
            return CategoryResolution('', phrase, '', 'unresolved', alternatives=tuple(sorted(ids)),
                                      reason=f'"{phrase}" could be {", ".join(sorted(ids))}; name one business.')
        cid, term = best[0]
        spec = CATEGORIES[cid]
        leftover = [w for w in re.findall(r"[\w'’]+", text)
                    if w not in NEUTRAL and not _contains(w, term.casefold())]
        if term.casefold() in GENERIC_HEADS and leftover:
            return CategoryResolution('', phrase, '', 'unresolved', alternatives=(cid,),
                                      reason=f'The modifier "{leftover[0]}" is not one CultureForge recognises, '
                                             f'so "{term}" was not read as {spec["label"].lower()}.')
        return CategoryResolution(cid, spec['label'], spec['query'], 'canonical', term,
                                  tuple(t.casefold() for t in spec['terms']), tuple(spec['adjacent']),
                                  f'"{phrase}" names the {spec["label"].lower()} category through "{term}".')
    words = re.findall(r"[\w'’]+", phrase)
    if 1 <= len(words) <= 4 and not all(w.casefold() in GENERIC_ONLY | NEUTRAL for w in words):
        return CategoryResolution('', phrase, phrase.casefold(), 'open_vocabulary', phrase.casefold(),
                                  tuple(w.casefold() for w in words if len(w) > 2), (),
                                  f'"{phrase}" is not a category CultureForge knows in advance, so Qloo\'s own '
                                  'taxonomy is asked what it is. It counts as resolved only if a returned '
                                  'category tag matches the phrase.')
    return CategoryResolution('', phrase, '', 'unresolved',
                              reason='The idea does not name one business CultureForge can look up.')


def attraction_hits(text: str) -> list[str]:
    return [t for t in ATTRACTION_TERMS if _contains(t, (text or '').casefold())]


def terms_for(category_id: str) -> tuple[str, ...]:
    return tuple(t.casefold() for t in CATEGORIES.get(category_id, {}).get('terms', ()))
