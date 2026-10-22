"""The published app must serve its UI and preserve API failures."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.main import http_error_handler
from backend.web import mount_frontend
from fastapi import HTTPException


@pytest.fixture
def published(tmp_path):
    (tmp_path / 'studio').mkdir()
    (tmp_path / 'assets').mkdir()
    (tmp_path / 'index.html').write_text('<h1>CultureForge</h1>')
    (tmp_path / 'studio' / 'index.html').write_text('<h1>Studio</h1>')
    (tmp_path / 'assets' / 'app-abc.js').write_text('console.log("studio")')
    app = FastAPI()
    app.add_exception_handler(HTTPException, http_error_handler)

    @app.get('/api/health')
    def health():
        return {'status': 'ok'}

    mount_frontend(app, str(tmp_path))
    return TestClient(app)


def test_both_entry_points_and_assets_are_published(published):
    assert 'CultureForge' in published.get('/').text
    assert 'Studio' in published.get('/studio/').text
    assert published.get('/').headers['cache-control'] == 'no-cache'
    assert 'immutable' in published.get('/assets/app-abc.js').headers['cache-control']
    assert published.get('/api/health').json() == {'status': 'ok'}


def test_missing_api_paths_do_not_become_frontend_html(published):
    response = published.get('/api/missing')
    assert response.status_code == 404
    assert response.json()['error']['code'] == 'NOT_FOUND'
    assert published.get('/assets/missing.js').status_code == 404
    assert published.get('/../requirements.txt').status_code == 404


def test_static_mount_preserves_wrong_api_method_status(published):
    response = published.delete('/api/health')
    assert response.status_code == 405
    assert response.headers['allow'] == 'GET'
    assert response.json()['detail']


def test_an_incomplete_build_fails_before_deployment(tmp_path):
    with pytest.raises(RuntimeError, match='npm run build'):
        mount_frontend(FastAPI(), str(tmp_path))
