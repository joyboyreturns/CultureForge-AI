from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import GenerateResponse, ProjectRequest
from .providers import QlooHarnessError, get_provider

app = FastAPI(title='CultureForge API', version='0.1.0')

# The frontend is served from a different port than the API whenever it is
# hosted as static files, so allow the usual local development origins. The
# Qloo credential never leaves the backend, so this exposes only the read-only
# project API.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r'http://(localhost|127\.0\.0\.1)(:\d+)?',
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
    allow_headers=['Content-Type'],
)


@app.get('/api/health')
def health():
    current_provider = get_provider()
    return {
        'status': 'ok',
        'dataMode': 'live' if current_provider.__class__.__name__ == 'QlooHarnessProvider' else 'mock',
    }


@app.get('/health', include_in_schema=False)
def health_alias():
    """Alias for tools that probe a conventional /health path."""
    return health()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a readable message instead of FastAPI's default error list.

    The frontend renders `detail` directly as the user-facing message, so a
    list of validation objects would be shown as a raw Python dict dump.
    """
    problems = []
    for error in exc.errors():
        location = '.'.join(str(part) for part in error.get('loc', []) if part != 'body')
        message = error.get('msg', 'Invalid value')
        problems.append(f'{location}: {message}' if location else message)
    return JSONResponse(status_code=422, content={'detail': '; '.join(problems) or 'Invalid request.'})


@app.post('/api/projects/generate', response_model=GenerateResponse)
def generate(project: ProjectRequest) -> GenerateResponse:
    try:
        return get_provider().generate(project)
    except QlooHarnessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
