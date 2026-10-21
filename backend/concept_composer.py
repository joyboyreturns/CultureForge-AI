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
FACET_DISTINCTIVE = 'distinctive'


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
        tagline='A rotating table where local makers set the menu.',
        offering='A shared counter and a changing roster of local makers, each holding one evening, with the Qloo-rated local venues acting as the talent pool and the sampling ground.',
        ritual='One maker, one evening, one dish the neighbourhood has not tried yet.',
        positioning='For an audience that values independent voices over a settled brand.',
        personality='Open, collaborative, unhurried',
        signals=['Independent discovery', 'Shared routines'],
        matchers=('independent', 'creator', 'maker', 'artist', 'design_conscious', 'design_focused', 'design_enthusiast', 'aspiring_designer'),
        type_matchers=('retail',),
        facet=FACET_DISTINCTIVE,
        accent='#bac49c',
        weight=1.2,
    ),
    Recipe(
        rule_id='slow-ritual',
        name='The Slow Hour',
        tagline='Low-light, low-volume, high-attention service.',
        offering='A deliberately unhurried format built around the most highly rated quiet venues in the brief, where the room, the pacing and the menu all stay small.',
        ritual='One long table, one course, and a rule against rushing anyone.',
        positioning='For an audience that buys restoration rather than entertainment.',
        personality='Calm, precise, restorative',
        signals=['Intentional rituals', 'Low-stimulation spaces'],
        matchers=('mindful', 'mindfulness', 'wellness', 'calm', 'slow', 'rest', 'psychological', 'focus', 'quiet'),
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
        offering='A concept built around design-conscious local venues, where the physical expression carries the brand and the programming follows the space rather than the other way round.',
        ritual='A monthly change of the room itself, announced the way a gallery announces a new show.',
        positioning='For an audience that treats taste as the primary signal of quality.',
        personality='Precise, confident, curated',
        signals=['Design-led spaces', 'Independent discovery'],
        matchers=('design', 'style', 'aesthetic', 'fashion', 'creative', 'culture', 'curated', 'artisan', 'premium'),
        type_matchers=('retail', 'hospitality'),
        facet=FACET_POPULARITY,
        accent='#e69b73',
        weight=1.15,
    ),
    Recipe(
        rule_id='community-table',
        name='The Neighbourhood Table',
        tagline='A long table that changes with who turns up.',
        offering='A community format anchored on the venues that already draw a crowd locally, with a shared table, a shared bill and a rotating host.',
        ritual='Whoever arrived first sets the first course.',
        positioning='For an audience that wants to belong to somewhere before it wants to buy from it.',
        personality='Generous, informal, local',
        signals=['Shared routines', 'Community & connection'],
        matchers=('community', 'family', 'supporting', 'together', 'local', 'neighbourhood', 'neighborhood', 'foodie', 'food', 'social', 'gathering'),
        type_matchers=('food', 'beverage', 'hospitality'),
        business_types=('Food & beverage', 'Retail', 'Hospitality'),
        facet=FACET_ACCESSIBLE,
        accent='#e69b73',
        weight=1.0,
    ),
    Recipe(
        rule_id='live-programme',
        name='The Late Programme',
        tagline='Culture as the headline act, not the decoration.',
        offering='A programming-led concept built on the most culturally active venues in the brief, where the offer is what happens in the room rather than what is on the table.',
        ritual='A different programme every week, chosen by the people who showed up last week.',
        positioning='For an audience that buys access to culture more than it buys objects.',
        personality='Restless, generous, current',
        signals=['Independent discovery', 'Hand-me-down culture'],
        matchers=('culture', 'cultural', 'music', 'night', 'event', 'discovery', 'explor', 'trend', 'curious', 'vibrant', 'energy'),
        type_matchers=('entertainment',),
        business_types=('Entertainment', 'Hospitality'),
        facet=FACET_DISTINCTIVE,
        accent='#b6b2da',
        weight=0.95,
    ),
    Recipe(
        rule_id='everyday-value',
        name='The Everyday Edit',
        tagline='Fewer things, chosen properly, priced honestly.',
        offering='A tight edit built on the most accessible of the returned venues, trading breadth for a price and a standard the founder can defend in public.',
        ritual='A fixed, published price and no upsell.',
        positioning='For an audience that has stopped paying for things it does not need.',
        personality='Straightforward, sturdy, plain-spoken',
        signals=['Practical utility', 'Transparent value'],
        matchers=('value', 'practical', 'afford', 'essential', 'everyday', 'budget', 'simple', 'frugal'),
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
        offering='An experience-first format built on the venues with the strongest local pull, where the offer is the hour spent there rather than the item carried away.',
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
        offering='A daytime-first format built on the venues that rate highest locally, with a short service, no music and a hard stop on the evening crowd.',
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


def _matches(recipe: Recipe, tag_names: list[str], business_type: str) -> tuple[float, list[str]]:
    """How strongly the evidence unlocks this recipe, and which tags did it."""
    if recipe.business_types and business_type not in recipe.business_types:
        return 0.0, []
    score = 0.0
    hit_tags: list[str] = []
    for tag in tag_names:
        for matcher in recipe.matchers:
            if matcher in tag:
                score += recipe.weight
                hit_tags.append(tag)
                break
    # The business type alone can unlock a direction, more weakly, so a brief
    # still yields directions when the audience tags are narrow.
    if not hit_tags:
        lowered = business_type.lower()
        if any(matcher in lowered for matcher in recipe.type_matchers):
            score += 0.5
    return score, hit_tags


def _facet_rank(facet: str, entities: list[dict]) -> list[dict]:
    """Order evidence by the facet this concept leans on."""
    if facet == FACET_RATING:
        return sorted(entities, key=lambda e: (_number(e.get('business_rating')), _number(e.get('popularity'))), reverse=True)
    if facet == FACET_ACCESSIBLE:
        priced = [e for e in entities if e.get('price_level') is not None]
        rest = [e for e in entities if e.get('price_level') is None]
        return sorted(priced, key=lambda e: (_number(e.get('price_level')), -_number(e.get('popularity')))) + sorted(
            rest, key=lambda e: _number(e.get('popularity')), reverse=True
        )
    if facet == FACET_DISTINCTIVE:
        return sorted(entities, key=lambda e: (len(e.get('description') or ''), _number(e.get('popularity'))), reverse=True)
    return sorted(entities, key=lambda e: (_number(e.get('popularity')), _number(e.get('business_rating'))), reverse=True)


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
    audience: str,
    location: str,
    budget: str,
    tags: list[dict],
    entities: list[dict],
    evidence_index: dict,
    tag_evidence_ids: dict,
    entity_evidence_ids: dict,
    trace_id: str,
) -> list[ComposedConcept]:
    """Build up to three distinct, evidence-backed directions.

    Returns fewer than three when the evidence only supports fewer. It never
    pads the set with catalog concepts: a half-supported answer is more
    honest than a full one.
    """
    tag_names = [_tag_name(tag.get('id', '')) for tag in tags]
    scored = []
    for recipe in RECIPES:
        score, hit_tags = _matches(recipe, tag_names, business_type)
        if score > 0:
            scored.append((score, recipe, hit_tags))
    if not scored:
        return []
    scored.sort(key=lambda item: -item[0])

    concepts: list[ComposedConcept] = []
    used_facets: set[str] = set()

    for _score, recipe, hit_tags in scored:
        if len(concepts) >= 3:
            break
        # Prefer directions that lean on a different facet of the evidence, so
        # the three are visibly distinct rather than three views of one venue.
        if recipe.facet in used_facets and len(concepts) < 2:
            continue
        ranked = _facet_rank(recipe.facet, entities)
        if not ranked:
            continue
        primary = ranked[0]
        support = [e for e in ranked[1:3] if _number(e.get('popularity')) > 0 or e.get('price_level') is not None]
        chosen = ([primary] + support)[:3]

        evidence_ids = []
        for entity in chosen:
            eid = entity_evidence_ids.get(entity.get('entity_id') or entity.get('id') or '')
            if eid:
                evidence_ids.append(eid)
        if not evidence_ids:
            continue

        primary_desc = _first_sentence(primary.get('description'))
        primary_label = primary.get('name') or 'the strongest local match'
        primary_rating = primary.get('business_rating')
        primary_popularity = primary.get('popularity')

        # The narrative cites the real returned venue, and its real attributes.
        descriptor_bits = []
        if primary_rating is not None:
            descriptor_bits.append(f'rated {primary_rating:g} locally')
        if primary_popularity is not None:
            descriptor_bits.append(f'popularity {primary_popularity:.3f}')
        descriptor = ' and '.join(descriptor_bits)

        description = (
            f'{recipe.offering} '
            f'The strongest local match in {location} is {primary_label}'
            + (f' ({descriptor})' if descriptor else '')
            + (f', described by Qloo as "{primary_desc}"' if primary_desc else '')
            + '.'
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
                'evidenceIds': evidence_ids[:2],
                'ruleId': recipe.rule_id,
                'origin': 'cultureforge_rule',
            },
        ]

        limitations = [
            'Qloo supplied the audience tags and the local entities. The business direction above is CultureForge’s interpretation, not a Qloo prediction.',
        ]
        if not any(_number(e.get('affinity')) != _number(chosen[0].get('affinity')) for e in chosen):
            limitations.append(
                'Qloo returned the same affinity for every candidate here, so affinity does not separate these venues. Popularity and local rating were used instead.'
            )

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
                    'Unlocked by ' + ', '.join(hit_tags[:3]) if hit_tags
                    else 'Unlocked by the ' + business_type.lower() + ' brief'
                ),
            )
        )
        used_facets.add(recipe.facet)

    return concepts
