from fastapi import FastAPI, HTTPException
from .models import GenerateResponse, ProjectRequest
from .providers import QlooHarnessError, get_provider, provider

app = FastAPI(title='CultureForge API', version='0.1.0')

@app.get('/api/health')
def health():
    current_provider = get_provider()
    return {'status': 'ok', 'dataMode': 'live' if current_provider.__class__.__name__ == 'QlooHarnessProvider' else 'mock'}

@app.post('/api/projects/generate', response_model=GenerateResponse)
def generate(project: ProjectRequest) -> GenerateResponse:
    try:
        return get_provider().generate(project)
    except QlooHarnessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
