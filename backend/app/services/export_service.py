"""
ECR-VP Export Service
====================
Creates tamper-evident ZIP bundles with:
- Corpus files with SHA-256 hashes
- Merkle tree binding all files together
- Human-readable PDF manifest
- Verification report PDF
- Corpus passport JSON

Merkle tree ensures: changing ANY single file invalidates the root hash.
"""

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ─── Merkle Tree ─────────────────────────────────────────────────

def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def sha256_pair(a: str, b: str) -> str:
    """Hash two hex strings together (Merkle node)."""
    combined = (a + b).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def build_merkle_tree(hashes: List[str]) -> Dict[str, Any]:
    """
    Build a Merkle tree from a list of leaf hashes.
    Returns: {
        "root": str,
        "leaves": [str],
        "levels": [[str], [str], ...],  # bottom to top
        "leaf_count": int
    }
    """
    if not hashes:
        return {"root": "", "leaves": [], "levels": [], "leaf_count": 0}

    levels = [list(hashes)]  # Level 0 = leaves

    current = list(hashes)
    while len(current) > 1:
        next_level = []
        for i in range(0, len(current), 2):
            if i + 1 < len(current):
                next_level.append(sha256_pair(current[i], current[i + 1]))
            else:
                # Odd element: pair with itself
                next_level.append(sha256_pair(current[i], current[i]))
        levels.append(next_level)
        current = next_level

    return {
        "root": current[0],
        "leaves": list(hashes),
        "levels": levels,
        "leaf_count": len(hashes),
    }


def verify_merkle_proof(leaf_hash: str, proof: List[Tuple[str, str]], root: str) -> bool:
    """Verify a Merkle proof for a single leaf."""
    current = leaf_hash
    for sibling, direction in proof:
        if direction == "left":
            current = sha256_pair(sibling, current)
        else:
            current = sha256_pair(current, sibling)
    return current == root


# ─── PDF Manifest ────────────────────────────────────────────────

def create_manifest_pdf(
    output_path: str,
    files_info: List[Dict[str, Any]],
    merkle_root: str,
    passport_id: str,
    session_id: str,
    interpreters: List[str],
    created_at: str,
):
    """
    Create a human-readable PDF manifest listing all corpus files,
    their SHA-256 hashes, and the Merkle root.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ManifestTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=6,
        textColor=HexColor("#1a1a2e"),
    )
    subtitle_style = ParagraphStyle(
        "ManifestSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=HexColor("#16213e"),
        spaceBefore=16,
        spaceAfter=8,
    )
    mono_style = ParagraphStyle(
        "Mono",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7,
        leading=10,
    )
    body_style = ParagraphStyle(
        "ManifestBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
    )
    small_style = ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontSize=7,
        textColor=HexColor("#999999"),
    )

    story = []

    # ── Header ──
    story.append(Paragraph("ECR-VP CORPUS VERIFICATION MANIFEST", title_style))
    story.append(Paragraph(
        f"Generated: {created_at} UTC | Protocol: ECR-VP v1.0",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#1a1a2e")))
    story.append(Spacer(1, 12))

    # ── Session Info ──
    story.append(Paragraph("SESSION INFORMATION", section_style))
    info_data = [
        ["Corpus Passport ID:", passport_id],
        ["Session ID:", session_id],
        ["Export Date:", created_at + " UTC"],
        ["Interpreters:", ", ".join(interpreters)],
        ["Total Files:", str(len(files_info))],
    ]
    info_table = Table(info_data, colWidths=[4.5 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # ── Merkle Root ──
    story.append(Paragraph("INTEGRITY SEAL (Merkle Root)", section_style))
    story.append(Paragraph(
        "The Merkle Root below is a single cryptographic hash that binds ALL files in this "
        "corpus together. Changing, replacing, or removing any single file will produce a "
        "different Merkle Root, proving tampering.",
        body_style,
    ))
    story.append(Spacer(1, 6))

    root_data = [["Merkle Root (SHA-256):", merkle_root]]
    root_table = Table(root_data, colWidths=[4.5 * cm, 12 * cm])
    root_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, 0), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 1, HexColor("#1a1a2e")),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f0f0f5")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(root_table)
    story.append(Spacer(1, 16))

    # ── File Table ──
    story.append(Paragraph("CORPUS FILES", section_style))
    story.append(Paragraph(
        "Each file is identified by its SHA-256 hash. The hashes below are the leaves "
        "of the Merkle tree whose root is shown above.",
        body_style,
    ))
    story.append(Spacer(1, 8))

    # Table header
    table_data = [["#", "Filename", "Size", "SHA-256"]]
    for i, fi in enumerate(files_info, 1):
        size_kb = fi["size_bytes"] / 1024
        if size_kb > 1024:
            size_str = f"{size_kb / 1024:.1f} MB"
        else:
            size_str = f"{size_kb:.0f} KB"

        # Truncate filename for table
        name = fi["filename"]
        if len(name) > 55:
            name = name[:52] + "..."

        table_data.append([
            str(i),
            Paragraph(name, ParagraphStyle("fn", fontSize=7, leading=9)),
            size_str,
            Paragraph(fi["sha256"], mono_style),
        ])

    file_table = Table(
        table_data,
        colWidths=[1 * cm, 7.5 * cm, 1.8 * cm, 6.5 * cm],
        repeatRows=1,
    )
    file_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGNMENT", (0, 0), (-1, 0), "CENTER"),
        # Body
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGNMENT", (0, 1), (0, -1), "CENTER"),
        ("ALIGNMENT", (2, 1), (2, -1), "RIGHT"),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f8f8fc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(file_table)
    story.append(Spacer(1, 20))

    # ── Verification Instructions ──
    story.append(Paragraph("HOW TO VERIFY", section_style))
    story.append(Paragraph(
        "1. Compute SHA-256 of each file in the corpus/ folder.<br/>"
        "2. Compare each hash with the table above.<br/>"
        "3. Rebuild the Merkle tree from the hashes (see MERKLE_TREE.json).<br/>"
        "4. The computed root must match the Merkle Root shown above.<br/>"
        "5. If ANY hash differs, the corpus has been tampered with.",
        body_style,
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        'Quick verify (Linux/Mac): sha256sum corpus/*.pdf | sort',
        mono_style,
    ))
    story.append(Paragraph(
        'Quick verify (Windows PowerShell): Get-FileHash corpus\\*.pdf -Algorithm SHA256',
        mono_style,
    ))
    story.append(Spacer(1, 20))

    # ── Footer ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This manifest was generated by ECR-VP (Epistemic Corpus Review &mdash; Verification Protocol). "
        "The Merkle tree cryptographically binds all corpus files together with the verification report. "
        "Any modification to any file will invalidate the integrity seal.",
        small_style,
    ))

    doc.build(story)


# ─── Report PDF ──────────────────────────────────────────────────

def create_report_pdf(
    output_path: str,
    report_text: str,
    interpreter_name: str,
    session_id: str,
    created_at: str,
):
    """Create a PDF version of the verification report."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=16,
        textColor=HexColor("#1a1a2e"),
    )
    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=16,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        spaceBefore=2,
        spaceAfter=2,
    )
    heading_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=HexColor("#16213e"),
        spaceBefore=14,
        spaceAfter=6,
    )

    story = []
    story.append(Paragraph("ECR-VP VERIFICATION REPORT", title_style))
    story.append(Paragraph(
        f"Interpreter: {interpreter_name} | Session: {session_id} | Date: {created_at} UTC",
        meta_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#1a1a2e")))
    story.append(Spacer(1, 12))

    # Parse report text into paragraphs
    lines = report_text.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 4))
        elif stripped.startswith("## ") or stripped.startswith("### "):
            clean = stripped.lstrip("#").strip()
            story.append(Paragraph(clean, heading_style))
        elif stripped.startswith("# "):
            clean = stripped.lstrip("#").strip()
            story.append(Paragraph(clean, heading_style))
        elif stripped.startswith("---") or stripped.startswith("==="):
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc")))
        else:
            # Escape XML special chars for reportlab
            safe = (
                stripped.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            # Restore bold markers as reportlab tags
            safe = safe.replace("**", "<b>", 1)
            while "**" in safe:
                safe = safe.replace("**", "</b>", 1)
                if "**" in safe:
                    safe = safe.replace("**", "<b>", 1)
            story.append(Paragraph(safe, body_style))

    doc.build(story)


# ─── ZIP Bundle Builder ──────────────────────────────────────────

def create_export_bundle(
    session_data: Dict[str, Any],
    corpus_files: List[str],
    output_dir: str,
) -> str:
    """
    Create a complete export ZIP bundle.

    Args:
        session_data: Session info including runs, passport, interpreters
        corpus_files: List of absolute paths to corpus PDF files
        output_dir: Where to save the ZIP file

    Returns:
        Path to the created ZIP file
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H%M%S")
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    session_id = session_data.get("session_id", "unknown")
    passport_id = session_data.get("passport_id", "unknown")

    # Collect interpreter names
    interpreters = []
    runs = session_data.get("runs", [])
    for run in runs:
        iname = run.get("interpreter", {}).get("provider", "unknown")
        model = run.get("interpreter", {}).get("model_id", "")
        interpreters.append(f"{iname}/{model}")

    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_dir = Path(tmpdir) / f"ECR-VP_Verification_{timestamp}"
        corpus_dir = bundle_dir / "corpus"
        corpus_dir.mkdir(parents=True)

        # ── 1. Copy corpus files & compute hashes ──
        files_info = []
        for filepath in sorted(corpus_files):
            src = Path(filepath)
            if not src.exists():
                continue

            dst = corpus_dir / src.name
            shutil.copy2(str(src), str(dst))

            file_hash = sha256_file(str(dst))
            files_info.append({
                "filename": src.name,
                "sha256": file_hash,
                "size_bytes": src.stat().st_size,
                "path_in_zip": f"corpus/{src.name}",
            })

        if not files_info:
            raise ValueError("No corpus files found to export")

        # ── 2. Build Merkle tree ──
        leaf_hashes = [fi["sha256"] for fi in files_info]
        merkle = build_merkle_tree(leaf_hashes)

        # ── 3. Create report PDFs (one per run) ──
        report_files = []
        for run in runs:
            provider = run.get("interpreter", {}).get("provider", "unknown")
            model_id = run.get("interpreter", {}).get("model_id", "unknown")
            raw_text = run.get("response", {}).get("raw_text", "")

            if not raw_text:
                continue

            safe_name = f"REPORT_{provider}_{model_id}".replace("/", "_").replace(".", "_")
            report_path = bundle_dir / f"{safe_name}.pdf"

            try:
                create_report_pdf(
                    str(report_path),
                    raw_text,
                    f"{provider}/{model_id}",
                    session_id,
                    date_str,
                )
                report_files.append(str(report_path))

                # Add report hash to Merkle tree
                report_hash = sha256_file(str(report_path))
                files_info.append({
                    "filename": report_path.name,
                    "sha256": report_hash,
                    "size_bytes": report_path.stat().st_size,
                    "path_in_zip": report_path.name,
                })
            except Exception as e:
                print(f"Warning: Failed to create report PDF for {provider}/{model_id}: {e}")

        # ── 4. Rebuild Merkle tree with reports included ──
        all_hashes = [fi["sha256"] for fi in files_info]
        merkle = build_merkle_tree(all_hashes)

        # ── 5. Save Merkle tree JSON ──
        merkle_data = {
            "version": "1.0",
            "algorithm": "SHA-256",
            "created_at": date_str,
            "session_id": session_id,
            "passport_id": passport_id,
            "merkle_root": merkle["root"],
            "leaf_count": merkle["leaf_count"],
            "leaves": [
                {
                    "index": i,
                    "filename": fi["filename"],
                    "sha256": fi["sha256"],
                    "size_bytes": fi["size_bytes"],
                }
                for i, fi in enumerate(files_info)
            ],
            "tree_levels": merkle["levels"],
            "verification_note": (
                "To verify: recompute SHA-256 of each file, "
                "rebuild the Merkle tree bottom-up, "
                "and compare the root hash."
            ),
        }
        merkle_path = bundle_dir / "MERKLE_TREE.json"
        with open(merkle_path, "w", encoding="utf-8") as f:
            json.dump(merkle_data, f, indent=2, ensure_ascii=False)

        # ── 6. Save passport JSON ──
        passport_data = session_data.get("passport", {})
        passport_data["export_merkle_root"] = merkle["root"]
        passport_data["export_timestamp"] = date_str
        passport_path = bundle_dir / "PASSPORT.json"
        with open(passport_path, "w", encoding="utf-8") as f:
            json.dump(passport_data, f, indent=2, ensure_ascii=False)

        # ── 7. Create manifest PDF ──
        manifest_path = bundle_dir / "CORPUS_MANIFEST.pdf"
        create_manifest_pdf(
            str(manifest_path),
            files_info,
            merkle["root"],
            passport_id,
            session_id,
            interpreters,
            date_str,
        )

        # ── 8. Create ZIP ──
        zip_name = f"ECR-VP_Verification_{timestamp}.zip"
        zip_path = Path(output_dir) / zip_name
        os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, filenames in os.walk(bundle_dir):
                for filename in filenames:
                    abs_path = Path(root) / filename
                    arc_name = abs_path.relative_to(bundle_dir)
                    zf.write(abs_path, arc_name)

        return str(zip_path)
