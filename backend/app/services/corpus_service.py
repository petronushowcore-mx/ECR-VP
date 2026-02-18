"""
ECR-VP Corpus Service

Handles corpus lifecycle: upload, hash, passport generation, immutability.
Implements Canon Lock per ECR-VP §2.5 and Engineering Spec §4.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..models.schema import (
    ArchitecturalStatus,
    CorpusFile,
    CorpusPassport,
)


class CorpusService:
    """
    Manages corpus files and generates Corpus Passports.
    
    Storage layout:
        data/corpora/{passport_id}/
            passport.json
            files/
                001_filename.pdf
                002_filename.md
                ...
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.corpora_dir = data_dir / "corpora"
        self.corpora_dir.mkdir(parents=True, exist_ok=True)

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def create_passport(
        self,
        files: list[Path],
        purpose: str,
        architectural_status: ArchitecturalStatus,
        canon_version: str,
        constraints: list[str] | None = None,
        snapshot_date: datetime | None = None,
    ) -> CorpusPassport:
        """
        Create a Corpus Passport from a list of files.
        Files are copied to immutable storage and hashed.
        
        This is the Canon Lock operation.
        After this, the corpus is frozen for the session.
        """
        passport = CorpusPassport(
            purpose=purpose,
            architectural_status=architectural_status,
            canon_version=canon_version,
            snapshot_date=snapshot_date or datetime.now(timezone.utc),
            constraints=constraints or [],
            files=[],  # Will be populated below
        )

        # Create storage directory
        corpus_dir = self.corpora_dir / passport.passport_id
        files_dir = corpus_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        # Process each file
        corpus_files = []
        for order, file_path in enumerate(files, start=1):
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Compute hash
            file_hash = self.compute_file_hash(file_path)
            
            # Copy to immutable storage with canonical ordering prefix
            dest_name = f"{order:03d}_{file_path.name}"
            dest_path = files_dir / dest_name
            shutil.copy2(file_path, dest_path)
            
            corpus_files.append(CorpusFile(
                filename=file_path.name,
                size_bytes=file_path.stat().st_size,
                sha256=file_hash,
                canonical_order=order,
                file_path=str(dest_path.relative_to(self.data_dir)),
            ))
        
        passport.files = corpus_files
        passport.lock()

        # Save passport as immutable JSON
        passport_path = corpus_dir / "passport.json"
        passport_path.write_text(
            passport.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return passport

    def load_passport(self, passport_id: str) -> CorpusPassport:
        """Load an existing passport by ID."""
        passport_path = self.corpora_dir / passport_id / "passport.json"
        if not passport_path.exists():
            raise FileNotFoundError(f"Passport not found: {passport_id}")
        
        data = json.loads(passport_path.read_text(encoding="utf-8"))
        return CorpusPassport(**data)

    def get_corpus_files(self, passport: CorpusPassport) -> list[tuple[CorpusFile, Path]]:
        """
        Get corpus files in canonical order, with full paths.
        Returns list of (CorpusFile metadata, absolute file path).
        """
        result = []
        for cf in sorted(passport.files, key=lambda f: f.canonical_order):
            full_path = self.data_dir / cf.file_path
            if not full_path.exists():
                raise FileNotFoundError(
                    f"Corpus file missing: {cf.filename} (expected at {full_path})"
                )
            # Verify integrity
            actual_hash = self.compute_file_hash(full_path)
            if actual_hash != cf.sha256:
                raise RuntimeError(
                    f"Integrity violation: {cf.filename} hash mismatch. "
                    f"Expected {cf.sha256}, got {actual_hash}. "
                    f"Corpus may have been tampered with."
                )
            result.append((cf, full_path))
        return result

    def verify_integrity(self, passport: CorpusPassport) -> dict[str, bool]:
        """
        Verify SHA-256 hashes of all corpus files.
        Returns dict of filename -> integrity_ok.
        """
        results = {}
        for cf in passport.files:
            full_path = self.data_dir / cf.file_path
            if not full_path.exists():
                results[cf.filename] = False
                continue
            actual_hash = self.compute_file_hash(full_path)
            results[cf.filename] = (actual_hash == cf.sha256)
        return results

    def list_passports(self) -> list[CorpusPassport]:
        """List all available corpus passports."""
        passports = []
        for corpus_dir in sorted(self.corpora_dir.iterdir()):
            passport_path = corpus_dir / "passport.json"
            if passport_path.exists():
                try:
                    data = json.loads(passport_path.read_text(encoding="utf-8"))
                    passports.append(CorpusPassport(**data))
                except Exception:
                    continue  # Skip corrupted passports
        return passports

    def passport_to_text(self, passport: CorpusPassport) -> str:
        """
        Generate human-readable Corpus Passport text for interpreter input.
        This is sent as the first message to each interpreter.
        """
        lines = [
            "═══ CORPUS PASSPORT ═══",
            f"Passport ID: {passport.passport_id}",
            f"Created: {passport.created_at.isoformat()}",
            f"Snapshot Date: {passport.snapshot_date.isoformat()}",
            f"Purpose: {passport.purpose}",
            f"Architectural Status: {passport.architectural_status.value}",
            f"Canon Version: {passport.canon_version}",
        ]
        
        if passport.constraints:
            lines.append(f"Constraints: {'; '.join(passport.constraints)}")
        
        lines.append(f"\nCorpus Files ({len(passport.files)} total):")
        for cf in sorted(passport.files, key=lambda f: f.canonical_order):
            lines.append(
                f"  [{cf.canonical_order:03d}] {cf.filename} "
                f"({cf.size_bytes:,} bytes, SHA-256: {cf.sha256[:16]}...)"
            )
        
        lines.append("═══ END CORPUS PASSPORT ═══")
        return "\n".join(lines)
