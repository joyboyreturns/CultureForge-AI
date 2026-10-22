"""Serve the built frontend from the API's origin, without masking API errors."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from starlette.staticfiles import StaticFiles
from starlette.routing import Match


class FrontendFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        # Unknown API routes must remain JSON 404s, even with the UI mounted.
        if path.split('/')[0] in {'api', 'health', 'docs', 'redoc', 'openapi.json'}:
            # A root static mount otherwise wins over the router's partial
            # method match, turning DELETE /api/health into a false 404.
            for route in scope['app'].routes:
                match, _ = route.matches(scope)
                if match == Match.PARTIAL:
                    raise HTTPException(status_code=405, detail='That method is not allowed for this API route.',
                                        headers={'Allow': ', '.join(sorted(route.methods or []))})
            raise HTTPException(status_code=404, detail='That API route does not exist.')
        response = await super().get_response(path, scope)
        if response.headers.get('content-type', '').startswith('text/html'):
            response.headers['Cache-Control'] = 'no-cache'
        elif path.startswith('assets/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        return response


def mount_frontend(app: FastAPI, directory: str) -> None:
    root = Path(directory).resolve()
    if not (root / 'index.html').is_file() or not (root / 'studio' / 'index.html').is_file():
        raise RuntimeError('The production frontend is missing. Run npm run build before starting the server.')
    app.mount('/', FrontendFiles(directory=str(root), html=True), name='frontend')
