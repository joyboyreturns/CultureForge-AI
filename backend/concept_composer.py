"""Deterministic concept composer.

The mock catalog decides what a business idea looks like before any data is
seen. This module inverts that: the Qloo evidence decides.

Qloo supplies two things:

* **the audience lens** - the tags returned by ``find_tags`` for the founder's
  audience description. These genuinely differ per audience, and they are what
  selects a recipe.
* **the local evidence** - the entities returned by ``recommend`` for the
  founder's location, each with a real name, description, popularity,
  affinity, rating, price level, geocode and image.

CultureForge supplies the third thing, and owns it: the business reading. A
recipe is a rule that says "when the evidence looks like this, here is a
business direction worth testing". Every rule names the evidence it used, so
the UI can show exactly which returned entity supports which proposal.

Nothing here is generated freely. A recipe only fires when the evidence
actually supports it, and a concept only ever cites evidence it was given.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional

# Tag families Qloo returns, keyed by the fragment that identifies them.
AUDIENCE_TAG_HINTS = (
    'customer_segment',
    'target_audience',
    'demographic',
    'lifestyle',
)

# Concepts are differentiated by which evidence facet they lean on, so that two
# concepts never end up citing the same venue for the same reason.
FACET_POPULARITY = 'popularity'
FACET_RATING = 'rating'
FACET_ACCESSIBLE = 'accessible'
# The returned place with the *lowest* Qloo popularity: of the places Qloo
# returned for this audience's signals, the least widely popular one. It is
# named for what it measures. It is not distinctiveness, independence or
# fit, none of which this ordering can see.
FACET_LEAST_MAINSTREAM = 'least_mainstream'

#: How each facet chose a direction's reference, as the direction states it.
#: Each sentence describes only an ordering of values Qloo returned.
FACET_BASIS = {
    FACET_POPULARITY: (
        'The reference was chosen as the returned place with the highest Qloo popularity, '
        'rating breaking ties. Popularity is general, not specific to this audience.'),
    FACET_RATING: (
        'The reference was chosen as the returned place with the highest Qloo business rating, '
        'popularity breaking ties.'),
    FACET_ACCESSIBLE: (
        'The reference was chosen as the returned place with the lowest Qloo price level; '
        'places without a returned price level follow, most popular first.'),
    FACET_LEAST_MAINSTREAM: (
        'The reference was chosen as the returned place with the lowest Qloo popularity, '
        'the least mainstream of the places returned for these audience signals. That is an '
        'ordering, not a measure of distinctiveness or independence.'),
}


@dataclass
class Recipe:
    """A business direction, and the evidence signature that unlocks it."""
    rule_id: str
    name: str
    tagline: str
    offering: str
    ritual: str
    positioning: str
    personality: str
    signals: list[str]
    # Any of these appearing in a Qloo tag name unlocks the recipe.
    matchers: tuple[str, ...]
    # Any of these appearing in the business type unlocks it more weakly, so a
    # brief still yields directions when the audience tags are narrow.
    type_matchers: tuple[str, ...] = ()
    business_types: tuple[str, ...] = ()
    facet: str = FACET_POPULARITY
    accent: str = '#e69b73'
    weight: float = 1.0


# The library. Every matcher is a fragment of a Qloo tag name, so a recipe fires
# because the audience actually resolved to that cultural signal.
RECIPES: tuple[Recipe, ...] = (
    Recipe(
        rule_id='independent-craft',
        name='Independent Makers Guild',
        tagline='A rotating showcase shaped by independent makers.',
        offering='A shared space and a changing roster of independent makers. The returned places provide cultural references for the proposed format; their availability as partners or suppliers has not been established.',
        ritual='One invited maker presents a small collection and explains the process behind it.',
        positioning='For an audience that values independent voices over a settled brand.',
        personality='Open, collaborative, unhurried',
        signals=['Independent discovery', 'Shared routines'],
        matchers=('independent', 'creator', 'maker', 'artist', 'design_conscious', 'design_focused', 'design_enthusiast', 'aspiring_designer'),
        type_matchers=('retail',),
        facet=FACET_LEAST_MAINSTREAM,
        accent='#bac49c',
        weight=1.2,
    ),
    Recipe(
        rule_id='slow-ritual',
        name='The Slow Hour',
        tagline='Low-light, low-volume, high-attention service.',
        offering='A deliberately unhurried format, proposed around the references Qloo returned — where the room, the pacing and the programme all stay small. Quietness was not measured.',
        ritual='One shared session, a small programme, and a rule against rushing anyone.',
        positioning='Proposed positioning: restoration rather than entertainment. Willingness to pay was not tested.',
        personality='Calm, precise, restorative',
        signals=['Intentional rituals', 'Low-stimulation spaces'],
        matchers=('mindful', 'mindfulness', 'wellness', 'calm', 'slow', 'rest', 'restorative',
                 'psychological', 'focus', 'quiet'),
        type_matchers=('wellness',),
        business_types=('Food & beverage', 'Wellness', 'Hospitality'),
        facet=FACET_RATING,
        accent='#b6b2da',
        weight=1.25,
    ),
    Recipe(
        rule_id='design-led',
        name='The Design Floor',
        tagline='A space that behaves like the thing it sells.',
        offering='A design-led format proposed from the returned reference places, where the physical expression carries the brand and the programming follows the space. These places were returned for the query; their design quality was not independently assessed.',
        ritual='A monthly change of the room itself, announced the way a gallery announces a new show.',
        positioning='For an audience that treats taste as the primary signal of quality.',
        personality='Precise, confident, curated',
        signals=['Design-led spaces', 'Independent discovery'],
        matchers=('design', 'designer', 'style', 'aesthetic', 'fashion', 'creative', 'curated'),
        type_matchers=('retail', 'hospitality'),
        facet=FACET_POPULARITY,
        accent='#e69b73',
        weight=1.15,
    ),
    Recipe(
        rule_id='community-table',
        name='The Shared Table',
        tagline='A long table that changes with who turns up.',
        offering='A community format anchored on the reference places returned for this query — local attendance was not measured — with a shared table, a shared bill and a rotating host.',
        ritual='Whoever arrived first sets the first course.',
        positioning='For an audience that wants to belong to somewhere before it wants to buy from it.',
        personality='Generous, informal, local',
        signals=['Shared routines', 'Community & connection'],
        matchers=('community', 'family', 'supporting', 'together', 'local', 'neighbourhood', 'neighborhood', 'foodie', 'food', 'social', 'gathering'),
        type_matchers=('food', 'beverage', 'hospitality'),
        business_types=('Food & beverage', 'Hospitality'),
        facet=FACET_ACCESSIBLE,
        accent='#e69b73',
        weight=1.0,
    ),
    Recipe(
        rule_id='live-programme',
        name='The Late Programme',
        tagline='Culture as the headline act, not the decoration.',
        offering='A programming-led concept built on the returned reference venues, used to propose a format where the offer is what happens in the room rather than what is on the table.',
        ritual='A different programme every week, chosen by the people who showed up last week.',
        positioning='For an audience that buys access to culture more than it buys objects.',
        personality='Restless, generous, current',
        signals=['Independent discovery', 'Hand-me-down culture'],
        matchers=('culture', 'cultural', 'music', 'night', 'event', 'discovery', 'explore',
                 'exploration', 'exploratory', 'trend', 'curious', 'curiosity', 'vibrant',
                 'energy', 'energetic'),
        type_matchers=('entertainment',),
        business_types=('Entertainment', 'Hospitality'),
        facet=FACET_LEAST_MAINSTREAM,
        accent='#b6b2da',
        weight=0.95,
    ),
    Recipe(
        rule_id='everyday-value',
        name='The Everyday Edit',
        tagline='Fewer things, chosen properly, priced honestly.',
        offering='A tightly edited offer with transparent prices, using returned price levels when available and popularity otherwise to select a reference. Affordability, accessibility and willingness to pay have not been measured.',
        ritual='A fixed, published price and no upsell.',
        positioning='For an audience that has stopped paying for things it does not need.',
        personality='Straightforward, sturdy, plain-spoken',
        signals=['Practical utility', 'Transparent value'],
        matchers=('value', 'values', 'practical', 'afford', 'affordable', 'affordability',
                 'essential', 'everyday', 'budget', 'simple', 'frugal'),
        type_matchers=('retail',),
        business_types=('Retail', 'Food & beverage'),
        facet=FACET_ACCESSIBLE,
        accent='#bac49c',
        weight=0.9,
    ),
    Recipe(
        rule_id='experience-led',
        name='The Third Place',
        tagline='A room that people come to be in, not just to buy from.',
        offering='An experience-first format built on the returned venues selected using Qloo popularity, not measured local demand, where the offer is the hour spent there rather than the item carried away.',
        ritual='No fixed closing time, and a seat that is always available for whoever is next.',
        positioning='For an audience that has run out of places to be.',
        personality='Energetic, open, unprogrammed',
        signals=['Community & connection', 'Novel experiences'],
        matchers=('social', 'gathering', 'experience', 'moment', 'vibrant', 'energy', 'third', 'belong', 'active', 'fun'),
        type_matchers=('food', 'beverage', 'hospitality', 'entertainment'),
        business_types=('Food & beverage', 'Hospitality', 'Entertainment', 'Retail'),
        facet=FACET_POPULARITY,
        accent='#e69b73',
        weight=0.85,
    ),
    Recipe(
        rule_id='quiet-hub',
        name='The Quiet Hub',
        tagline='A daytime room that behaves like a good desk.',
        offering='A proposed daytime format referencing highly rated places in the returned sample, with short sessions and low-stimulation programming. The references do not establish local suitability or measured quietness.',
        ritual='A two-hour sitting that ends with the same time every day.',
        positioning='For an audience whose taste is expressed in restraint.',
        personality='Measured, understated, exacting',
        signals=['Intentional rituals', 'Personal pace'],
        matchers=('professional', 'remote', 'work', 'focus', 'quiet', 'mindful', 'wellness', 'balance', 'calm', 'simple'),
        type_matchers=('wellness', 'hospitality'),
        business_types=('Wellness', 'Hospitality', 'Food & beverage'),
        facet=FACET_RATING,
        accent='#b6b2da',
        weight=0.8,
    ),
)


@dataclass
class ComposedConcept:
    name: str
    tagline: str
    description: str
    offering: str
    ritual: str
    positioning: str
    personality: str
    signals: list[str]
    accent: str
    image: str
    image_alt: str
    evidence_ids: list[str] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    rationale: str = ''
    #: One sentence about why this direction fits this audience, written by
    #: the language model. Empty when the model was not used, in which case
    #: the recipe's own positioning is shown instead.
    naming: str = ''


def _tag_name(tag_id: str) -> str:
    """'urn:tag:customer_segment:qloo:gen_z_foodies' -> 'gen z foodies'."""
    tail = tag_id.rsplit(':', 1)[-1]
    return tail.replace('_', ' ').strip()


#: A matcher is a whole word or a whole phrase. "rest" is a word; it is not
#: the first four letters of "restaurant", and a rule that cannot tell the
#: difference is a rule that fires on the wrong evidence.
def _whole_words(matcher: str, text: str) -> bool:
    phrase = matcher.replace('_', ' ').strip()
    if not phrase:
        return False
    pattern = r'\b' + r'\s+'.join(re.escape(word) for word in phrase.split()) + r'\b'
    return re.search(pattern, text) is not None


def _matches(recipe: Recipe, tag_names: list[str], business_type: str) -> tuple[float, list[str]]:
    """How strongly the evidence unlocks this recipe, and which tags did it."""
    if recipe.business_types and business_type not in recipe.business_types:
        return 0.0, []
    score = 0.0
    hit_tags: list[str] = []
    for tag in tag_names:
        for matcher in recipe.matchers:
            if _whole_words(matcher, tag):
                score += recipe.weight
                hit_tags.append(tag)
                break
    return score, hit_tags


#: The words Qloo uses in its own descriptions when the entity is an
#: organisation rather than a place someone goes to. A park-managing
#: nonprofit is not a dining room, and building a direction around one
#: because it came back with a high local rating is how the evidence chain
#: stops meaning anything.
_ORGANISATION_WORDS = (
    'nonprofit', 'non-profit', 'organization', 'organisation', 'corporation',
    'company', 'foundation', 'agency', 'authority', 'department', 'llc',
    'inc.', 'inc ', 'trust', 'association', 'society', 'consortium',
)


def _is_organisation(entity: dict) -> bool:
    """Whether Qloo's own description says this is an organisation."""
    text = (entity.get('description') or '').lower()
    if not text:
        return False
    head = text[:160]
    return any(word in head for word in _ORGANISATION_WORDS)


def _facet_rank(facet: str, entities: list[dict]) -> list[dict]:
    """Order evidence by the facet this concept leans on.

    Organisations come last in every ordering. They stay in the evidence —
    Qloo returned them, and hiding that would be its own kind of lie — but
    they do not become the place a direction is built around.
    """
    def by_organisation(rows: list[dict]) -> list[dict]:
        # An organisation is never the place a direction is built around, so
        # it sorts after every place.
        return sorted(rows, key=lambda e: _is_organisation(e))

    if facet == FACET_RATING:
        return by_organisation(sorted(
            entities, key=lambda e: (_number(e.get('business_rating')), _number(e.get('popularity'))),
            reverse=True))
    if facet == FACET_ACCESSIBLE:
        priced = [e for e in entities if e.get('price_level') is not None]
        rest = [e for e in entities if e.get('price_level') is None]
        return by_organisation(sorted(
            priced, key=lambda e: (_number(e.get('price_level')), -_number(e.get('popularity')))) + sorted(
            rest, key=lambda e: _number(e.get('popularity')), reverse=True))
    if facet == FACET_LEAST_MAINSTREAM:
        # Lowest returned popularity first. A place without a positive
        # popularity value has none to order by, so it follows the others.
        known = [e for e in entities if _number(e.get('popularity')) > 0]
        unknown = [e for e in entities if _number(e.get('popularity')) <= 0]
        return by_organisation(sorted(
            known, key=lambda e: (_number(e.get('popularity')), -_number(e.get('business_rating'))))
            + sorted(unknown, key=lambda e: _number(e.get('business_rating')), reverse=True))
    return by_organisation(sorted(
        entities, key=lambda e: (_number(e.get('popularity')), _number(e.get('business_rating'))),
        reverse=True))


def _number(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _first_sentence(text: Optional[str], limit: int = 180) -> str:
    if not text:
        return ''
    trimmed = text.strip()
    if len(trimmed) <= limit:
        return trimmed
    cut = trimmed[:limit]
    stop = cut.rfind('. ')
    if stop > 60:
        cut = cut[: stop + 1]
    return cut + '…'


def compose(
    *,
    business_type: str,
    business_idea: str = '',
    audience: str,
    location: str,
    budget: str,
    tags: list[dict],
    entities: list[dict],
    evidence_index: dict,
    tag_evidence_ids: dict,
    entity_evidence_ids: dict,
    trace_id: str,
    crossdomain: Optional[list[dict]] = None,
) -> list[ComposedConcept]:
    """Build up to three distinct, evidence-backed directions.

    Returns fewer than three when the evidence only supports fewer. It never
    pads the set with catalog concepts: a half-supported answer is more
    honest than a full one.
    """
    from .relevance import assess, brief_family
    tag_names = [_tag_name(tag.get('id', '')) for tag in tags]
    family = brief_family(business_type, business_idea, audience)
    eligible = []
    for entity in entities:
        relevance = entity.get('relevance') or assess(
            business_type=business_type, idea=business_idea, audience=audience,
            location=location, name=entity.get('name') or '',
            description=entity.get('description') or '',
            has_identifier=bool(entity.get('entity_id') or entity.get('id')))
        if relevance['anchorEligible']:
            eligible.append(entity)
    if not eligible:
        return []
    scored = []
    for recipe in RECIPES:
        score, hit_tags = _matches(recipe, tag_names, business_type)
        if score > 0:
            scored.append((score, recipe, hit_tags))
    # Specific formats depend on both a brief occasion and a direct returned
    # category reference. The occasion is the founder's hypothesis, not a
    # behavior inferred from Qloo. Missing opening hours remain an explicit gap.
    if family == 'bakery':
        bread_tags = [tag for tag in tag_names if any(_whole_words(word, tag)
                      for word in ('bread', 'bakery', 'artisan', 'croissant', 'baking'))]
        if bread_tags:
            if any(_whole_words(word, audience.lower()) for word in ('commuters', 'commuter', 'morning', 'early')):
                scored.append((5, Recipe(
                    rule_id='bakery-morning-collection', name='The Morning Bread Counter',
                    tagline='A bread collection format to test around the morning journey.',
                    offering='An artisan bakery with a focused takeaway bread offer and preordered collection. The morning occasion comes from your brief; Qloo supplies category-relevant references, not commuter demand.',
                    ritual='Pilot a collection window with the audience in the brief; measure repeat collection before expanding.',
                    positioning='A proposed quick-collection occasion for the commuters described in the brief.',
                    personality='Focused, practical, welcoming', signals=['Bread craft', 'Morning collection hypothesis'],
                    matchers=(), facet=FACET_ACCESSIBLE), bread_tags))
            scored.append((4, Recipe(
                rule_id='bakery-craft-counter', name='The Bread Workshop',
                tagline='A craft-led bread offer with the making process in view.',
                offering='An artisan bakery with a small bread range and a visible making process. Returned bakery references and bread-related audience seeds support exploring this category; enthusiasm for demonstrations is untested.',
                ritual='Offer a small bread tasting and ask visitors whether the process adds value before building a programme.',
                positioning='A proposed craft-discovery occasion, with products and process as the focus.',
                personality='Precise, tactile, curious', signals=['Bread craft', 'Process discovery hypothesis'],
                matchers=(), facet=FACET_RATING), bread_tags))
    if not scored:
        return []
    scored.sort(key=lambda item: -item[0])

    concepts: list[ComposedConcept] = []
    used_facets: set[str] = set()
    # The three directions have to be visibly different, not three views of
    # one venue. A place that is already the anchor of a direction is not
    # used as the anchor of another.
    used_anchors: set[str] = set()

    for _score, recipe, hit_tags in scored:
        if len(concepts) >= 3:
            break
        # Prefer directions that lean on a different facet of the evidence, so
        # the three are visibly distinct rather than three views of one venue.
        if recipe.facet in used_facets and len(concepts) < 2:
            continue
        ranked = _facet_rank(recipe.facet, eligible)
        if not ranked:
            continue
        # An organisation Qloo described as an organisation does not become
        # the place a business is built around. It stays in the evidence, and
        # the direction is built from the places instead.
        places = [e for e in ranked if not _is_organisation(e)]
        if not places:
            continue
        fresh = [e for e in places
                 if (e.get('entity_id') or e.get('id')) not in used_anchors]
        if not fresh:
            continue
        primary = fresh[0]
        support = [e for e in places[1:3]
                   if (e.get('entity_id') or e.get('id')) != (primary.get('entity_id') or primary.get('id'))
                   and (_number(e.get('popularity')) > 0 or e.get('price_level') is not None)]
        chosen = ([primary] + support)[:3]
        used_anchors.add(primary.get('entity_id') or primary.get('id') or '')

        evidence_ids = []
        for entity in chosen:
            eid = entity_evidence_ids.get(entity.get('entity_id') or entity.get('id') or '')
            if eid:
                evidence_ids.append(eid)
        if not evidence_ids:
            continue

        primary_desc = _first_sentence(primary.get('description'))
        primary_label = primary.get('name') or 'the reference selected for this direction'
        primary_rating = primary.get('business_rating')
        primary_popularity = primary.get('popularity')

        # The narrative cites the real returned venue, and its real attributes.
        descriptor_bits = []
        if primary_rating is not None:
            descriptor_bits.append(f'rated {primary_rating:g} by Qloo')
        if primary_popularity is not None:
            descriptor_bits.append(f'popularity {primary_popularity:.3f}')
        descriptor = ' and '.join(descriptor_bits)

        # The reference was returned for the location query. Qloo returning it
        # does not establish that it is the strongest match, or that it sits
        # inside the location, so the wording says only what is true.
        description = (
            (f'Proposed for {business_idea} in {location}. ' if business_idea else '')
            + f'{recipe.offering} '
            f'The reference selected for this direction is {primary_label}'
            + (f' ({descriptor})' if descriptor else '')
            + (f', described by Qloo as "{primary_desc}"' if primary_desc else '')
            + f'. It was returned by Qloo for a {location} query; the location it belongs to '
              'was not verified.'
        )

        decisions = [
            {
                'id': f'{recipe.rule_id}-offering',
                'field': 'offering',
                'proposal': recipe.offering,
                'evidenceIds': evidence_ids,
                'ruleId': recipe.rule_id,
                'origin': 'cultureforge_rule',
            },
            {
                'id': f'{recipe.rule_id}-ritual',
                'field': 'signature ritual',
                'proposal': recipe.ritual,
                'evidenceIds': evidence_ids[:1],
                'ruleId': recipe.rule_id,
                'origin': 'cultureforge_rule',
            },
            {
                'id': f'{recipe.rule_id}-positioning',
                'field': 'positioning',
                'proposal': recipe.positioning,
                'evidenceIds': evidence_ids[:1] + [tag_evidence_ids[tag.get('id')] for tag in tags
                    if _tag_name(tag.get('id', '')) in hit_tags and tag.get('id') in tag_evidence_ids],
                'ruleId': recipe.rule_id,
                'origin': 'cultureforge_rule',
            },
        ]
        # Cross-domain responses stay in the audience bridge. Sharing the
        # audience seeds does not establish a relationship to this particular
        # proposal, so no automatic bridge-to-decision citations are added.

        limitations = [
            'Qloo supplied the audience tags and the returned entities. The business direction above is CultureForge’s interpretation, not a Qloo prediction.',
            'Category relevance uses returned text, not a validated business match. Opening hours, commuter access, demand and willingness to pay are unverified. A field test rejecting the proposed occasion would change this direction.',
        ]
        skipped = [e.get('name') for e in entities if _is_organisation(e) and e.get('name')]
        if skipped:
            limitations.append(
                'Qloo also returned '
                + ', '.join(skipped[:2])
                + ', which its own description calls an organisation rather than a place to '
                  'go to. It is in the evidence and it was not used as the anchor here.'
            )
        if not any(_number(e.get('affinity')) != _number(chosen[0].get('affinity')) for e in chosen):
            limitations.append(
                'Qloo returned the same affinity for every candidate here, so affinity does not separate these venues.'
            )
        basis = FACET_BASIS[recipe.facet] + ' This ordering is restricted to category-relevant references.'
        if (primary.get('entity_id') or primary.get('id')) != (places[0].get('entity_id') or places[0].get('id')):
            basis += ' The first such place already anchors another direction, so the next one was used.'
        limitations.append(basis)

        concepts.append(
            ComposedConcept(
                name=recipe.name,
                tagline=recipe.tagline,
                description=description,
                offering=recipe.offering,
                ritual=recipe.ritual,
                positioning=recipe.positioning,
                personality=recipe.personality,
                signals=list(recipe.signals),
                accent=recipe.accent,
                image=primary.get('image') or '',
                image_alt=f'{primary_label}, returned by Qloo for this audience and location',
                evidence_ids=evidence_ids,
                decisions=decisions,
                limitations=limitations,
                rationale=(
                    'Unlocked by ' + ', '.join(hit_tags[:3]) + f'; proposed for {audience} in {location}. The audience occasion is from the brief, not inferred behavior.' if hit_tags
                    else 'Unlocked by the ' + business_type.lower() + ' brief'
                ),
            )
        )
        used_facets.add(recipe.facet)

    return concepts
