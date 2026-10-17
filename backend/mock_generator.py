"""Deterministic mock generation. Keep rules aligned with src/mockData.ts."""
import json
import re
from pathlib import Path
from uuid import uuid4
from .models import Concept, CulturalSignal, ExperienceMoment, GenerateResponse, ProjectRequest, ProvenanceMetadata

CATALOG = json.loads((Path(__file__).resolve().parent.parent / 'shared' / 'mockCatalog.json').read_text())

def normalize(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()

def fingerprint(value: str) -> int:
    return sum(ord(char) * (index + 1) for index, char in enumerate(normalize(value))) % 10000

def clamp(value: int) -> int:
    return max(65, min(96, value))

def round_positive(value: float) -> int:
    # Match JavaScript Math.round for positive pilot-budget values.
    return int(value + 0.5)

def investment(budget: str, factor: float) -> str:
    if budget.startswith('Under'):
        low, high = 12, 22
    elif '100k+' in budget:
        low, high = 110, 170
    elif '50k – $100k' in budget:
        low, high = 55, 88
    elif '25k – $50k' in budget:
        low, high = 28, 46
    else:
        low, high = 25, 50
    return f'${round_positive(low * factor)}–{round_positive(high * factor)}k pilot'

def generate_mock(project: ProjectRequest) -> GenerateResponse:
    words = f' {normalize(project.audience)} '
    ranked = [(profile, [keyword for keyword in profile['keywords'] if f' {keyword} ' in words]) for profile in CATALOG['profiles']]
    ranked.sort(key=lambda item: len(item[1]), reverse=True)
    profile, matches = ranked[0] if ranked[0][1] else (CATALOG['profiles'][-1], [])
    business = CATALOG['businesses'][project.businessType]
    seed = fingerprint(project.audience)
    objective = project.objectives[0].strip() if project.objectives and project.objectives[0].strip() else 'Learn what resonates with this audience'
    rationale = (f"Mock audience lens: {profile['label']}. Matched words: {', '.join(matches)}. This is a template rule, not a measured audience preference." if matches else f'No predefined audience keywords matched. These mock directions use your brief “{project.audience}” and a general pilot-and-feedback approach; no preferences are inferred.')
    delivery = profile['delivery'][project.businessType]
    concepts = []
    for index, template in enumerate(business['templates']):
        descriptions = [f'Prototype this signature moment with a small group drawn from your audience brief: {project.audience}.', delivery, f'Trial this in {project.location} and collect feedback against your objective: {objective}.']
        concepts.append(Concept(
            id=f"{business['slug']}-{profile['id']}-{seed}-{index + 1}", direction=f'{index + 1:02d}',
            name=profile['names'][project.businessType][index], tagline=template['tagline'],
            description=template['offering'] + (f' Audience brief: “{project.audience}”.' if profile['id'] == 'general' else '') + f' {delivery}',
            audienceFit=clamp(profile['fits'][index] + (seed + index * 3) % 5 - 2),
            culturalRelevance=clamp(84 + (seed + index * 7) % 11), feasibility=clamp(86 - index * 3 + (seed + index) % 5),
            budget=project.budget, investment=investment(project.budget, template['costFactor']),
            signals=[profile['signals'][0][0], template['theme'], profile['signals'][1][0]],
            accent=CATALOG['accents'][index], image=template['image'], imageAlt=template['imageAlt'], personality=template['personality'],
            audienceRationale=rationale,
            implementationNote=f'Proposed pilot in {project.location}. Test the objective “{objective}” within {project.budget}. The displayed range is an illustrative pilot allowance, not a validated full-business startup cost.',
            moments=[ExperienceMoment(title=title, description=descriptions[i]) for i, title in enumerate(template['moments'])],
        ))
    return GenerateResponse(
        projectId=f'cf-{uuid4().hex[:10]}', project=project, concepts=concepts,
        signals=[CulturalSignal(label=label, detail=f'Mock hypothesis to test: {hypothesis}. Audience brief: {project.audience}.', score=78 + (seed + index * 5) % 15, category='Mock assumption') for index, (label, hypothesis) in enumerate(profile['signals'])],
        dataMode='mock', conceptMode='sample',
        notice=f"Rule-based mock generation for {project.businessType} using the “{profile['label']}” lens. Concepts, cultural hypotheses, scores, and pilot budgets are illustrative. Qloo is not connected to this mock run.",
        provenance=ProvenanceMetadata(source='Mock'),
    )
