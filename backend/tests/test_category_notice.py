"""An idea the rules cannot name is said plainly, with no direction and no widening.

The held Qloo envelopes are passed in directly, and the cross-domain bridge
calls are answered empty, so this runs the real composition path offline.
"""
from backend.models import ProjectRequest
from backend.providers import QlooHarnessProvider


def _generate(monkeypatch, recommend_places, idea, audience='Food explorers'):
    def held_only(self, operation, payload):
        return {'status': 'ok', 'results': []}, False, 1

    monkeypatch.setattr(QlooHarnessProvider, 'run_workflow_cached', held_only)
    project = ProjectRequest(businessType='Food & beverage', businessIdea=idea, audience=audience,
                             location='Tokyo, Japan', budget='$25k – $50k', objectives=['Attract a new audience'])
    tags = {'status': 'ok', 'results': [{'id': 'urn:tag:interests:qloo:food_explorers'}]}
    return QlooHarnessProvider().generate(project, tag_result=tags, recommendations=recommend_places)


def test_an_unrecognised_idea_gives_no_direction_and_names_the_idea(monkeypatch, recommend_places):
    response = _generate(monkeypatch, recommend_places, idea='Shop')
    assert response.concepts == []
    assert 'does not recognise "Shop"' in response.notice
    steps = {event.step: event for event in response.trace}
    assert steps['classify-business-category'].status == 'skipped'
    assert '"Shop"' in steps['classify-business-category'].detail
    assert 'not widened' in steps['classify-business-category'].detail


def test_a_recognised_idea_is_classified_and_not_called_unrecognised(monkeypatch, recommend_places):
    response = _generate(monkeypatch, recommend_places, idea='Gelato shop')
    steps = {event.step: event for event in response.trace}
    assert steps['classify-business-category'].status == 'ok'
    assert 'names a frozen dessert category' in steps['classify-business-category'].detail
    assert 'does not recognise' not in response.notice
