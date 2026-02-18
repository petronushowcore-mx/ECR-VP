"""
ECR-VP Export Router
====================
Adds /api/sessions/{session_id}/export endpoint
Returns a ZIP bundle with Merkle-tree-bound corpus + report.

Add to main.py:
    from app.routers.export_router import router as export_router
    app.include_router(export_router, prefix="/api")
"""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

# Adjust imports to match your project structure:
# from app.services.export_service import create_export_bundle
# from app.services.corpus_service import CorpusService
# from app.services.session_service import SessionService

router = APIRouter(tags=["export"])


@router.get("/sessions/{session_id}/export")
async def export_session(session_id: str):
    """
    Export a completed session as a verification ZIP bundle.
    
    The bundle contains:
    - corpus/ — all original PDFs with SHA-256 hashes
    - CORPUS_MANIFEST.pdf — human-readable file list + hashes
    - MERKLE_TREE.json — full Merkle tree for tamper detection
    - REPORT_*.pdf — verification report(s) from interpreter(s)
    - PASSPORT.json — corpus passport with Merkle root
    
    Returns: ZIP file download
    """
    # ─── Import here to avoid circular imports ───
    # Uncomment and adjust these imports for your actual project structure:
    from app.services.export_service import create_export_bundle
    
    # ─── 1. Load session data ───
    # Replace with your actual session/corpus loading logic:
    try:
        # Example: get session from your session service
        # session = session_service.get_session(session_id)
        # For now, showing the expected data structure:
        
        from app.services.session_service import get_session_by_id
        session = get_session_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        if session.get("state") != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Session is not completed (state: {session.get('state')})"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load session: {str(e)}")

    # ─── 2. Get corpus file paths ───
    try:
        # Replace with your actual corpus file resolution:
        # corpus_files = corpus_service.get_file_paths(session["passport_id"])
        
        passport_id = session.get("passport_id", "")
        corpus_dir = session.get("corpus_dir", "")
        
        if corpus_dir and os.path.isdir(corpus_dir):
            corpus_files = [
                str(Path(corpus_dir) / f)
                for f in os.listdir(corpus_dir)
                if f.lower().endswith(".pdf")
            ]
        else:
            # Fallback: try to get from session segments
            corpus_files = []
            for seg in session.get("segments", []):
                fpath = seg.get("file_path", "")
                if fpath and os.path.exists(fpath):
                    corpus_files.append(fpath)
        
        if not corpus_files:
            raise HTTPException(
                status_code=400,
                detail="No corpus files found for this session"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve corpus files: {str(e)}")

    # ─── 3. Prepare session data dict ───
    session_data = {
        "session_id": session_id,
        "passport_id": passport_id,
        "runs": [],
        "passport": session.get("passport", {}),
    }
    
    for run in session.get("runs", []):
        session_data["runs"].append({
            "interpreter": {
                "provider": run.get("provider", run.get("interpreter", {}).get("provider", "unknown")),
                "model_id": run.get("model_id", run.get("interpreter", {}).get("model_id", "unknown")),
            },
            "response": {
                "raw_text": run.get("raw_text", run.get("response", {}).get("raw_text", "")),
            },
        })

    # ─── 4. Create export bundle ───
    try:
        export_dir = os.path.join(tempfile.gettempdir(), "ecr-vp-exports")
        zip_path = create_export_bundle(session_data, corpus_files, export_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create export: {str(e)}")

    # ─── 5. Return ZIP file ───
    filename = os.path.basename(zip_path)
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
