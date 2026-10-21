import pytest

from backend.challenge_probe import challenge_probe
from backend.models import (
    ChallengeProbeRequest, ChallengeRevision, Concept, Evidence, ProjectRequest,
)
from backend.providers import QlooHarnessError


def _request(direction_id='direction-a', tags=None):
    evidence = [
        Evidence(id='place-a', kind='entity', label='Anchor Place', entityId='entity-a', entityType='place'),
        Evidence(id='place-b', kind='entity', label='Other Place', entityId='entity-b', entityType='place'),
        Evidence(id='tag-a', kind='tag', label='Food design', tagId='urn:tag:interests:qloo:food_design'),
    ]
    concept = Concept(
        id='direction-a', name='Direction A', tagline='A tagline', description='A direction',
        budget='small', investment='pilot', signals=['food design'], accent='green', image='',
        evidenceIds=['place-a', 'place-b'],
    )
    return ChallengeProbeRequest(
        project=ProjectRequest(businessType='Food & beverage', audience='Gen Z foodies',
                               location='Brooklyn, New York', budget='small'),
        directionId=direction_id,
        revision=ChallengeRevision(evidence=evidence, concepts=[concept], resolvedTags=(
            ['urn:tag:interests:qloo:food_design'] if tags is None else tags)),
    )


class FakeProvider:
    def __init__(self, envelope=None, error=None, cached=False, requests=1):
        self.envelope = envelope or {'results': {'entities': [
            {'entity_id': 'entity-c', 'name': 'Replacement Place', 'affinity': 0.72},
        ]}}
        self.error = error
        self.cached = cached
        self.requests = requests
        self.payloads = []

    def run_insights_probe_cached(self, payload):
        self.payloads.append(payload)
        if self.error:
            raise self.error
        return self.envelope, self.cached, self.requests

    @staticmethod
    def rows(envelope):
        rows = envelope.get('results', [])
        if isinstance(rows, dict):
            rows = rows.get('entities', rows.get('tags', []))
        return rows if isinstance(rows, list) else []

    @staticmethod
    def _affinity(row):
        return row.get('affinity')


def test_probe_builds_fixed_exclusion_query_and_keeps_result_unresolved():
    provider = FakeProvider()
    result = challenge_probe(_request(), provider)

    assert len(provider.payloads) == 1
    query = provider.payloads[0]
    assert query == {
        'filter.type': 'urn:entity:place',
        'signal.interests.tags': 'urn:tag:interests:qloo:food_design',
        'operator.signal.interests.tags': 'intersection',
        'signal.location.query': 'Brooklyn, New York',
        'filter.exclude.entities': 'entity-a',
        'take': 5,
        'feature.explainability': True,
    }
    assert result['anchor']['entityId'] == 'entity-a'
    assert [row.entityId for row in result['replacements']] == ['entity-c']
    assert result['outcome'] == 'unresolved'
    assert result['transportRequests'] == 1


def test_invalid_direction_spends_no_workflow():
    provider = FakeProvider()
    with pytest.raises(QlooHarnessError, match='not part'):
        challenge_probe(_request('missing'), provider)
    assert provider.payloads == []


def test_missing_audience_tags_spends_no_workflow():
    provider = FakeProvider()
    with pytest.raises(QlooHarnessError, match='valid Qloo audience tags'):
        challenge_probe(_request(tags=[]), provider)
    assert provider.payloads == []


def test_empty_bounded_response_is_unresolved_not_rejected():
    provider = FakeProvider({'results': {'entities': []}}, requests=1)
    result = challenge_probe(_request(), provider)
    assert result['outcome'] == 'unresolved'
    assert result['replacements'] == []
    assert 'not proof of absence' in result['falsifier']


def test_cached_probe_reports_zero_new_requests():
    provider = FakeProvider(cached=True, requests=0)
    result = challenge_probe(_request(), provider)
    assert result['cached'] is True
    assert result['transportRequests'] == 0


def test_provider_failure_propagates_without_changing_direction():
    error = QlooHarnessError('Qloo unavailable.', code='PROVIDER_UNAVAILABLE', retryable=True)
    provider = FakeProvider(error=error)
    with pytest.raises(QlooHarnessError) as caught:
        challenge_probe(_request(), provider)
    assert caught.value is error
    assert provider.payloads
