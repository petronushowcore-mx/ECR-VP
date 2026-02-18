"""
ECR-VP Execution Shell — FastAPI Application

REST API for the ECR-VP protocol execution shell.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .models.schema import (
    ArchitecturalStatus,
    InterpreterConfig,
    VerificationSession,
)
from .services.corpus_service import CorpusService
from .services.orchestrator import SessionOrchestrator

# Import providers to trigger registration
from .providers import anthropic_provider, openai_provider, ollama_provider  # noqa: F401
from .core.gateway import ProviderRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────────────────

DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ─── Services ────────────────────────────────────────────────────────────

corpus_service = CorpusService(DATA_DIR)
orchestrator = SessionOrchestrator(corpus_service, DATA_DIR)

# ─── App ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ECR-VP Execution Shell starting...")
    logger.info(f"Data directory: {DATA_DIR.absolute()}")
    logger.info(f"Available providers: {ProviderRegistry.list_available()}")
    yield
    logger.info("ECR-VP Execution Shell shutting down.")


app = FastAPI(
    title="ECR-VP Execution Shell",
    description=(
        "Orchestration shell for the ECR-VP v1.0 protocol. "
        "Executes the protocol, preserves invariants, produces auditable artifacts. "
        "Does NOT interpret, evaluate, or synthesize."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ─────────────────────────────────────────────

class CreatePassportRequest(BaseModel):
    purpose: str
    architectural_status: ArchitecturalStatus
    canon_version: str
    constraints: list[str] = []
    file_ids: list[str] = []  # If empty, includes ALL uploaded files


class CreateSessionRequest(BaseModel):
    passport_id: str
    interpreters: list[InterpreterConfig]


class ExecuteSessionRequest(BaseModel):
    parallel: bool = True


class HealthResponse(BaseModel):
    status: str
    providers: list[str]
    data_dir: str


# ─── Routes: Health ──────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        providers=ProviderRegistry.list_available(),
        data_dir=str(DATA_DIR.absolute()),
    )


# ─── Routes: License Validation ────────────────────────────────────────

class ValidateLicenseRequest(BaseModel):
    license_key: str
    instance_name: Optional[str] = "ecr-vp-shell"

@app.post("/api/license/validate")
async def validate_license(req: ValidateLicenseRequest):
    """
    Validate a license key via LemonSqueezy API.
    
    BYOK model: user buys license on LemonSqueezy, enters key here.
    Key is validated server-side (to prevent client-side bypass)
    but NEVER stored to disk.
    """
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.lemonsqueezy.com/v1/licenses/validate",
                json={
                    "license_key": req.license_key,
                    "instance_name": req.instance_name,
                },
            )
            data = resp.json()
            
            if data.get("valid"):
                return {
                    "valid": True,
                    "license_key_short": req.license_key[:5] + "..." + req.license_key[-4:],
                    "status": data.get("license_key", {}).get("status", "active"),
                    "customer_name": data.get("meta", {}).get("customer_name"),
                    "product_name": data.get("meta", {}).get("product_name"),
                    "variant_name": data.get("meta", {}).get("variant_name"),
                    "expires_at": data.get("license_key", {}).get("expires_at"),
                }
            else:
                return {
                    "valid": False,
                    "error": data.get("error", "Invalid or expired license key"),
                }
    except httpx.TimeoutException:
        # If LemonSqueezy is unreachable, allow grace period
        logger.warning("LemonSqueezy API timeout — granting grace access")
        return {
            "valid": True,
            "status": "grace",
            "error": "License server unreachable. Grace access granted.",
        }
    except Exception as e:
        logger.error(f"License validation error: {e}")
        raise HTTPException(status_code=502, detail="License server error")


# ─── Routes: File Upload ─────────────────────────────────────────────────

@app.post("/api/files/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Upload corpus files. Returns file IDs for passport creation."""
    uploaded = []
    for file in files:
        # Save to upload directory
        file_path = UPLOAD_DIR / file.filename
        content = await file.read()
        file_path.write_bytes(content)
        
        uploaded.append({
            "filename": file.filename,
            "size_bytes": len(content),
            "file_id": file.filename,  # Simple ID for now
            "path": str(file_path),
        })
    
    return {"uploaded": uploaded}


@app.get("/api/files")
async def list_uploaded_files():
    """List all uploaded files available for corpus creation."""
    files = []
    for f in sorted(UPLOAD_DIR.iterdir()):
        if f.is_file():
            files.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "file_id": f.name,
            })
    return {"files": files}


@app.delete("/api/files/{file_id}")
async def delete_uploaded_file(file_id: str):
    """Delete an uploaded file from the corpus staging area."""
    import urllib.parse
    decoded = urllib.parse.unquote(file_id)
    file_path = UPLOAD_DIR / decoded
    if not file_path.exists():
        raise HTTPException(404, f"File not found: {decoded}")
    file_path.unlink()
    return {"deleted": decoded}


# ─── Routes: Corpus Passport ────────────────────────────────────────────

@app.post("/api/passports")
async def create_passport(request: CreatePassportRequest):
    """Create a Corpus Passport (Canon Lock)."""
    # If no file_ids provided, use ALL uploaded files
    file_ids = request.file_ids
    if not file_ids:
        file_ids = [f.name for f in sorted(UPLOAD_DIR.iterdir()) if f.is_file()]
    
    if not file_ids:
        raise HTTPException(400, "No files uploaded. Upload files first.")
    
    # Resolve file paths
    file_paths = []
    for file_id in file_ids:
        path = UPLOAD_DIR / file_id
        if not path.exists():
            raise HTTPException(404, f"File not found: {file_id}")
        file_paths.append(path)
    
    logger.info(f"Creating passport with {len(file_paths)} files")
    
    try:
        passport = corpus_service.create_passport(
            files=file_paths,
            purpose=request.purpose,
            architectural_status=request.architectural_status,
            canon_version=request.canon_version,
            constraints=request.constraints,
        )
        return {
            "passport_id": passport.passport_id,
            "created_at": passport.created_at.isoformat(),
            "files_count": len(passport.files),
            "is_locked": passport.is_locked,
        }
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/api/passports")
async def list_passports():
    """List all corpus passports."""
    passports = corpus_service.list_passports()
    return {
        "passports": [
            {
                "passport_id": p.passport_id,
                "created_at": p.created_at.isoformat(),
                "purpose": p.purpose,
                "architectural_status": p.architectural_status.value,
                "canon_version": p.canon_version,
                "files_count": len(p.files),
            }
            for p in passports
        ]
    }


@app.get("/api/passports/{passport_id}")
async def get_passport(passport_id: str):
    """Get full passport details."""
    try:
        passport = corpus_service.load_passport(passport_id)
        return passport.model_dump()
    except FileNotFoundError:
        raise HTTPException(404, f"Passport not found: {passport_id}")


@app.get("/api/passports/{passport_id}/verify")
async def verify_passport_integrity(passport_id: str):
    """Verify SHA-256 integrity of all corpus files."""
    try:
        passport = corpus_service.load_passport(passport_id)
        integrity = corpus_service.verify_integrity(passport)
        all_ok = all(integrity.values())
        return {
            "passport_id": passport_id,
            "integrity_ok": all_ok,
            "files": integrity,
        }
    except FileNotFoundError:
        raise HTTPException(404, f"Passport not found: {passport_id}")


# ─── Routes: Sessions ───────────────────────────────────────────────────

@app.post("/api/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a verification session from a passport and interpreter configs."""
    try:
        passport = corpus_service.load_passport(request.passport_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Passport not found: {request.passport_id}")
    
    try:
        session = orchestrator.create_session(passport, request.interpreters)
        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "runs": [
                {
                    "run_id": r.run_id,
                    "provider": r.interpreter.provider,
                    "model": r.interpreter.model,
                    "state": r.state.value,
                }
                for r in session.runs
            ],
        }
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/sessions/{session_id}/execute")
async def execute_session(session_id: str, request: ExecuteSessionRequest):
    """Execute all interpreter runs in a session."""
    try:
        session = orchestrator.load_session(session_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Session not found: {session_id}")
    
    try:
        session = await orchestrator.execute_session(session, parallel=request.parallel)
        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "runs": [
                {
                    "run_id": r.run_id,
                    "provider": r.interpreter.provider,
                    "model": r.interpreter.model,
                    "state": r.state.value,
                    "error": r.error,
                    "modes_detected": (
                        [m.mode for m in r.response.detected_modes]
                        if r.response else []
                    ),
                    "modes_missing": r.response.missing_modes if r.response else [],
                }
                for r in session.runs
            ],
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/sessions")
async def list_sessions():
    """List all verification sessions."""
    return {"sessions": orchestrator.list_sessions()}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full session details including run results."""
    try:
        session = orchestrator.load_session(session_id)
        return session.model_dump()
    except FileNotFoundError:
        raise HTTPException(404, f"Session not found: {session_id}")


@app.get("/api/sessions/{session_id}/runs/{run_id}/response")
async def get_run_response(session_id: str, run_id: str):
    """Get the raw immutable response from a specific interpreter run."""
    try:
        session = orchestrator.load_session(session_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Session not found: {session_id}")
    
    run = next((r for r in session.runs if r.run_id == run_id), None)
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    if not run.response:
        raise HTTPException(404, "No response captured for this run")
    
    return {
        "run_id": run_id,
        "provider": run.interpreter.provider,
        "model": run.interpreter.model,
        "raw_text": run.response.raw_text,
        "captured_at": run.response.captured_at.isoformat(),
        "token_count_input": run.response.token_count_input,
        "token_count_output": run.response.token_count_output,
        "detected_modes": [m.model_dump() for m in run.response.detected_modes],
        "missing_modes": run.response.missing_modes,
        "modes_in_order": run.response.modes_in_order,
    }


# ─── Routes: Providers ──────────────────────────────────────────────────

@app.get("/api/providers")
async def list_providers():
    """List available LLM providers."""
    return {"providers": ProviderRegistry.list_available()}


# ─── Static File Serving (Production Mode) ───────────────────────────
# When frontend is built (npm run build) and copied to backend/static/,
# FastAPI serves it directly. No separate frontend server needed.

STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.is_dir():
    from fastapi.responses import FileResponse

    # Serve static assets
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
