"""
ECR-VP Session Orchestrator

Manages the full protocol execution lifecycle:
1. Create session from passport
2. Launch isolated interpreter runs
3. Enforce sequential loading
4. Capture immutable artifacts
5. Transition to synthesis state

This is the core engine. It enforces protocol invariants
but does NOT interpret, evaluate, or synthesize results.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..core.gateway import (
    FilePayload,
    InterpreterProvider,
    MessagePayload,
    ProviderRegistry,
)
from ..models.schema import (
    CorpusPassport,
    InterpreterConfig,
    InterpreterResponse,
    InterpreterRun,
    ProtocolMode,
    RunState,
    SessionState,
    SessionType,
    VerificationSession,
)
from .corpus_service import CorpusService

logger = logging.getLogger(__name__)


# ─── Fixed Protocol Constants ────────────────────────────────────────

COMPLETION_PHRASE = (
    "Corpus completed. Execute the ECR-VP protocol. "
    "Do not ask clarifying questions. Do not request additional data. "
    "Work strictly by modes."
)

COMPLETION_PHRASE_FORMALIZATION = (
    "Corpus completed. Execute the formalization protocol. "
    "Do not ask clarifying questions. Do not request additional data. "
    "Translate to formal structures only."
)

COMPLETION_PHRASE_AGGREGATOR = (
    "All interpreter outputs provided above. Execute the divergence analysis. "
    "Do not ask clarifying questions. Map convergence and divergence only."
)

# ─── Prompt Templates (FIXED ARTIFACTS) ──────────────────────────────

# Mode 1: Strict Verifier — the original ECR-VP 8-mode prompt
STRICT_VERIFIER_PROMPT = '''You are acting as an independent interpreter within the ECR-VP verification protocol for an architectural document corpus. Your task is to produce a report on structural integrity, readability without the author, clarity of boundaries, engineering realizability of the core, and risks of over-claiming. You do not prove mathematical correctness and do not validate scientific results. You build a map of understanding and non-understanding. You do not optimize conclusions toward the author's expectations. You do not provide patent strategy advice. You do not ask for clarifications and do not request additional files. You work strictly by the modes described below and do not mix them.

Rc Mode: Describe what this architecture is as a class. What problems it addresses. How it differs from RL, planning, safe-RL, constrained optimization, and monitoring. Provide an interpretation without attempting to confirm correctness.

Ri Mode: Extract invariants and prohibitions explicitly fixed by the corpus. Formulate what must exist in the system and what is forbidden. If boundaries are unclear, indicate this. Anything not directly supported by the corpus must be marked as a hypothesis and placed in Rc.

Declarative Epistemic Typology Mode: Classify the corpus by epistemic layers using the fixed typology defined in the protocol. This mode is declarative and non-evaluative. Its purpose is to identify which layers are present, partially present, or absent, and where they manifest in the corpus. You must use the provided canonical list of layers and must not introduce new categories. This mode permits the use of a single table or a single bullet list strictly for semantic classification. No judgments, recommendations, or conclusions are allowed inside the table/list. After the classification, provide a short continuous-text explanation identifying (a) where layers are mixed without explicit marking, and (b) which missing layers may affect the stated maturity or applicability of the corpus. Do not assess quality. Do not propose improvements. Do not reinterpret authorial intent.

Ra Mode: Assess engineering realizability: what can be implemented as middleware/governor layers over existing systems today; what is possible only with domain-specific manual specification; what is declared but non-operational without additional definitions. Do not use philosophy here. Speak in terms of observable quantities, interfaces, integration modes, and test types.

Failure Mode: Describe likely failure modes: where the architecture could become a second control loop; where metric gaming could emerge; where non-causal observation could break; where definitional drift may occur; where over-promising risks are visible.

Novelty and Positioning Mode: Identify what appears genuinely non-trivial at the architectural class level and why. Distinguish structural novelty from terminological novelty. Indicate which elements are strongest candidates for grants or whitepapers as engineering innovation.

Verdict Mode: Provide a concise engineering verdict: how coherent the corpus is; how readable it is without the author; how realizable the core is; where the main gaps lie. The verdict must be short and without pathos.

Project Maturity Summary Mode: Provide a short operational summary of the project's maturity. This mode must be written as a single continuous text of approximately 5-10 sentences. Answer strictly the following questions: (1) What constitutes the engineering core of the architecture. (2) What minimal demonstrator or pilot could be built today without inventing missing definitions. (3) What missing specifications, interfaces, or criteria currently block grants, pilots, or engineering deployment. Do not repeat earlier analysis. Do not justify the author. Do not use philosophical language. This is not a verdict and not a recommendation, but an operational readiness snapshot.

Format: Write in continuous prose, in paragraphs, without bullet points. Separate modes with headings. Do not imitate the author's style. Do not compliment. Do not provide 'how to sell' advice. Act as a strict independent reviewer.'''

# Mode 3: Formalization — translate theory to formal structures
FORMALIZATION_PROMPT = '''You are acting as a formalization engine within the ECR-VP protocol. Your task is to translate the architectural theory in the provided corpus into machine-checkable formal structures.

For each major construct, definition, or mechanism in the corpus, produce one or more of the following:

1. Formal Definitions: Precise set-theoretic or type-theoretic definitions. Use standard mathematical notation. If the corpus uses informal language, translate it. If ambiguity exists, state the ambiguity explicitly and provide the closest unambiguous formalization.

2. Pseudocode: Algorithmic descriptions of processes, transitions, and decision procedures described in the corpus. Use a clean pseudocode style (Python-like or Haskell-like). Include type signatures where possible.

3. Constraint Specifications: Formal statements of invariants, preconditions, postconditions, and safety properties. Use predicate logic or temporal logic notation as appropriate.

4. Type Signatures: For every operator, function, or mapping described in the corpus, provide explicit type signatures showing domain, codomain, and any constraints.

5. Dependency Graph: Identify which definitions depend on which. Flag circular dependencies explicitly.

Rules:
- Do not evaluate the theory. Do not assess quality or correctness.
- Do not generate new theory. Only formalize what the corpus contains.
- If a concept cannot be formalized without additional definitions, state exactly what is missing.
- If the corpus contains contradictory definitions, formalize both and mark the contradiction.
- Separate each formalized construct with a clear heading referencing the source document and section.
- Write in continuous prose between formal blocks. Do not use bullet points for explanations.

Format: Organize by source document, then by construct. Use LaTeX-style notation for mathematics. Use code blocks for pseudocode. Act as a precise formalization instrument, not a critic.'''

# Mode 2: Position Aggregator — map divergence across interpreter outputs
AGGREGATOR_PROMPT = '''You are acting as a position aggregator within the ECR-VP protocol. You have received the outputs of multiple independent interpreters who each analyzed the same corpus under identical conditions, in complete isolation from each other.

Your task is to produce a structured divergence map. You do not evaluate the corpus itself. You do not add your own analysis of the source material. You only analyze the interpreter outputs.

Produce the following sections:

Consensus Zone: Identify claims, observations, or assessments that appear in a majority (>50%) of interpreter outputs. State each consensus point and note which interpreters support it.

Divergence Zone: Identify points where interpreters disagree or reach contradictory conclusions. For each divergence, state the positions of each interpreter. Do not resolve the disagreement. Do not pick a winner.

Unique Observations: Identify observations that appear in only one interpreter's output and are absent from all others. Note which interpreter made each unique observation.

Structural Compliance: For each interpreter, note whether they followed the prescribed mode structure, which modes they covered, and where they deviated from protocol.

Blind Spots: Identify topics or aspects of the corpus that no interpreter addressed, or that all interpreters treated superficially.

Confidence Distribution: For each major topic area, provide a rough distribution of how confidently interpreters assessed it (strong claims vs. hedged language vs. silence).

Rules:
- Do not evaluate the corpus directly. Your only input is interpreter outputs.
- Do not favor any interpreter over another.
- Do not generate recommendations or improvements.
- Quote specific interpreter statements only when necessary to illustrate divergence.
- Write in continuous prose, in paragraphs. Separate sections with headings.
- This is a convenience layer for human comprehension, not a verification instrument.

Format: Organize by the sections above. Be concise. Act as a neutral cartographer of positions, not a judge.'''


class SessionOrchestrator:
    """
    Orchestrates ECR-VP verification sessions.

    Key invariants enforced:
    - All interpreters receive identical input (same passport, prompt, corpus, order)
    - No interpreter sees output from another (except in Aggregator mode)
    - No prompt adaptation per model
    - All outputs are immutable once captured
    """

    # Map session types to their prompts
    PROMPT_MAP = {
        SessionType.STRICT_VERIFIER: STRICT_VERIFIER_PROMPT,
        SessionType.FORMALIZATION: FORMALIZATION_PROMPT,
        SessionType.POSITION_AGGREGATOR: AGGREGATOR_PROMPT,
    }

    COMPLETION_MAP = {
        SessionType.STRICT_VERIFIER: COMPLETION_PHRASE,
        SessionType.FORMALIZATION: COMPLETION_PHRASE_FORMALIZATION,
        SessionType.POSITION_AGGREGATOR: COMPLETION_PHRASE_AGGREGATOR,
    }

    def __init__(self, corpus_service: CorpusService, data_dir: Path):
        self.corpus_service = corpus_service
        self.data_dir = data_dir
        self.sessions_dir = data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        passport: CorpusPassport,
        interpreters: list[InterpreterConfig],
        session_type: SessionType = SessionType.STRICT_VERIFIER,
        source_session_id: Optional[str] = None,
    ) -> VerificationSession:
        """
        Create a new verification session.

        Args:
            passport: Locked Corpus Passport
            interpreters: List of interpreter configurations
            session_type: Type of session (strict_verifier, formalization, position_aggregator)
            source_session_id: For aggregator mode — ID of the session to analyze
        """
        if not passport.is_locked:
            raise ValueError("Cannot create session with unlocked passport. Run Canon Lock first.")

        if len(interpreters) < 1:
            raise ValueError("At least one interpreter is required.")

        # Validate session-type-specific requirements
        if session_type == SessionType.POSITION_AGGREGATOR:
            if not source_session_id:
                raise ValueError("Position Aggregator requires a source_session_id.")
            # Verify source session exists and is completed
            try:
                source = self.load_session(source_session_id)
                if source.state not in (SessionState.AWAITING_SYNTHESIS, SessionState.COMPLETED):
                    raise ValueError(
                        f"Source session must be in awaiting_synthesis or completed state, "
                        f"got {source.state.value}"
                    )
            except FileNotFoundError:
                raise ValueError(f"Source session not found: {source_session_id}")

        if session_type == SessionType.STRICT_VERIFIER and len(interpreters) < 3:
            logger.warning(
                "ECR-VP recommends at least 3 interpreters for Strict Verifier "
                f"(preferably 5). Only {len(interpreters)} configured."
            )

        # Select the appropriate prompt
        prompt = self.PROMPT_MAP[session_type]

        session = VerificationSession(
            passport=passport,
            reference_prompt=prompt,
            session_type=session_type,
            source_session_id=source_session_id,
            state=SessionState.LOCKED,
        )

        # Create runs for each interpreter
        for config in interpreters:
            run = InterpreterRun(
                session_id=session.session_id,
                interpreter=config,
                prompt_hash=InterpreterProvider.hash_prompt(prompt),
            )
            session.runs.append(run)

        # Save session
        self._save_session(session)

        logger.info(
            f"Session {session.session_id} created: type={session_type.value}, "
            f"interpreters={len(interpreters)}"
        )
        return session

    async def execute_session(
        self,
        session: VerificationSession,
        parallel: bool = True,
    ) -> VerificationSession:
        """
        Execute all interpreter runs in a session.

        Args:
            session: The session to execute
            parallel: If True, run interpreters concurrently; if False, sequentially
        """
        if session.state != SessionState.LOCKED:
            raise ValueError(f"Session must be in LOCKED state, got {session.state}")

        session.state = SessionState.EXECUTING
        self._save_session(session)

        if parallel:
            tasks = [
                self._execute_run(session, run)
                for run in session.runs
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            for run in session.runs:
                await self._execute_run(session, run)

        # Check if all runs completed
        all_done = all(
            r.state in (RunState.COMPLETED, RunState.FAILED)
            for r in session.runs
        )

        if all_done:
            session.state = SessionState.AWAITING_SYNTHESIS

        self._save_session(session)
        return session

    async def _execute_run(
        self,
        session: VerificationSession,
        run: InterpreterRun,
    ) -> None:
        """Execute a single interpreter run with full protocol compliance."""
        provider = ProviderRegistry.create(run.interpreter)

        try:
            run.state = RunState.LOADING
            run.started_at = datetime.now(timezone.utc)

            # Step 1: Create clean session
            provider_session_id = await provider.create_session()
            run.corpus_loading_log.append(f"Session created: {provider_session_id}")

            # Step 2: Send Corpus Passport
            passport_text = self.corpus_service.passport_to_text(session.passport)
            await provider.send_message(
                provider_session_id,
                MessagePayload(text=passport_text),
            )
            run.corpus_loading_log.append("Passport sent")

            # Step 3: Send reference prompt
            await provider.send_message(
                provider_session_id,
                MessagePayload(text=f"Reference prompt:\n\n{session.reference_prompt}"),
            )
            run.corpus_loading_log.append("Reference prompt sent")

            # Step 4: Send corpus files in canonical order
            corpus_files = self.corpus_service.get_corpus_files(session.passport)

            # Determine if we need sequential loading
            total_size = sum(cf.size_bytes for cf, _ in corpus_files)
            needs_sequential = self._needs_sequential_loading(
                provider, total_size, len(corpus_files)
            )

            if needs_sequential:
                # Sequential loading mode
                for i, (cf, file_path) in enumerate(corpus_files, 1):
                    file_content = file_path.read_bytes()

                    preamble = (
                        f"Corpus segment {i}/{len(corpus_files)}: {cf.filename}\n"
                        "Do not form final conclusions until the completion phrase is received."
                    )

                    await provider.send_message(
                        provider_session_id,
                        MessagePayload(
                            text=preamble,
                            files=[FilePayload(
                                filename=cf.filename,
                                content=file_content,
                                mime_type=self._guess_mime_type(cf.filename),
                                canonical_order=cf.canonical_order,
                            )],
                        ),
                    )
                    run.corpus_loading_log.append(
                        f"Segment {i}/{len(corpus_files)} sent: {cf.filename}"
                    )
            else:
                # Batch loading — send all files at once
                files = []
                for cf, file_path in corpus_files:
                    files.append(FilePayload(
                        filename=cf.filename,
                        content=file_path.read_bytes(),
                        mime_type=self._guess_mime_type(cf.filename),
                        canonical_order=cf.canonical_order,
                    ))

                await provider.send_message(
                    provider_session_id,
                    MessagePayload(
                        text="Full corpus attached below. Files are in canonical order.",
                        files=files,
                    ),
                )
                run.corpus_loading_log.append("Full corpus sent in batch mode")

            # Step 4.5: For Aggregator mode — inject source session outputs
            if session.session_type == SessionType.POSITION_AGGREGATOR and session.source_session_id:
                source_outputs = self._collect_source_outputs(session.source_session_id)
                await provider.send_message(
                    provider_session_id,
                    MessagePayload(text=source_outputs),
                )
                run.corpus_loading_log.append(
                    f"Source session outputs injected from {session.source_session_id}"
                )

            # Step 5: Send completion phrase and receive response
            run.state = RunState.AWAITING_RESPONSE
            completion = self.COMPLETION_MAP[session.session_type]
            response = await provider.send_and_receive(
                provider_session_id,
                MessagePayload(text=completion),
            )
            run.corpus_loading_log.append("Completion phrase sent, response received")

            # Step 6: Detect mode structure (for strict verifier only)
            if session.session_type == SessionType.STRICT_VERIFIER:
                response.detected_modes = self._detect_modes(response.raw_text)
                response.missing_modes = self._find_missing_modes(response.detected_modes)
                response.modes_in_order = self._check_mode_order(response.detected_modes)

            # Step 7: Store as immutable artifact
            run.response = response
            run.state = RunState.COMPLETED
            run.completed_at = datetime.now(timezone.utc)

            self._save_artifact(session, run)

            # Step 8: Close provider session
            await provider.close_session(provider_session_id)

        except Exception as e:
            run.state = RunState.FAILED
            run.error = str(e)
            run.completed_at = datetime.now(timezone.utc)
            logger.error(f"Run {run.run_id} failed: {e}", exc_info=True)

        finally:
            self._save_session(session)

    def _collect_source_outputs(self, source_session_id: str) -> str:
        """Collect all interpreter outputs from a source session for aggregator mode."""
        source = self.load_session(source_session_id)
        parts = [
            "=== INTERPRETER OUTPUTS FROM SOURCE SESSION ===\n"
            f"Source session: {source_session_id}\n"
            f"Session type: {source.session_type.value}\n"
            f"Number of interpreters: {len(source.runs)}\n"
        ]

        for i, run in enumerate(source.runs, 1):
            parts.append(f"\n{'='*60}")
            parts.append(f"INTERPRETER {i}: {run.interpreter.display_name}")
            parts.append(f"Provider: {run.interpreter.provider} / {run.interpreter.model}")
            parts.append(f"State: {run.state.value}")
            parts.append(f"{'='*60}\n")

            if run.response:
                parts.append(run.response.raw_text)
            elif run.error:
                parts.append(f"[FAILED: {run.error}]")
            else:
                parts.append("[No response captured]")

        parts.append(f"\n{'='*60}")
        parts.append("=== END OF INTERPRETER OUTPUTS ===")

        return "\n".join(parts)

    # ─── Mode Detection (Structural, Non-Evaluative) ─────────────────

    def _detect_modes(self, text: str) -> list:
        """
        Detect protocol mode boundaries in interpreter output.
        This is structural detection — NOT content evaluation.
        """
        from ..models.schema import DetectedMode
        import re

        modes = []
        # Look for mode headings — interpreters typically use these patterns
        patterns = [
            (ProtocolMode.RC, r"(?:^|\n)\s*#+\s*Rc\s+Mode[:\s]", r"Rc Mode"),
            (ProtocolMode.RI, r"(?:^|\n)\s*#+\s*Ri\s+Mode[:\s]", r"Ri Mode"),
            (ProtocolMode.DECLARATIVE_TYPOLOGY,
             r"(?:^|\n)\s*#+\s*Declarative\s+Epistemic\s+Typology[:\s]",
             r"Declarative Epistemic Typology"),
            (ProtocolMode.RA, r"(?:^|\n)\s*#+\s*Ra\s+Mode[:\s]", r"Ra Mode"),
            (ProtocolMode.FAILURE, r"(?:^|\n)\s*#+\s*Failure\s+Mode[:\s]", r"Failure Mode"),
            (ProtocolMode.NOVELTY,
             r"(?:^|\n)\s*#+\s*Novelty\s+(?:and|&)\s+Positioning[:\s]",
             r"Novelty and Positioning"),
            (ProtocolMode.VERDICT, r"(?:^|\n)\s*#+\s*Verdict[:\s]", r"Verdict Mode"),
            (ProtocolMode.MATURITY,
             r"(?:^|\n)\s*#+\s*Project\s+Maturity\s+Summary[:\s]",
             r"Project Maturity Summary"),
        ]

        for mode, pattern, heading in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                modes.append(DetectedMode(
                    mode=mode.value,
                    start_position=match.start(),
                    end_position=match.end(),
                    heading_text=heading,
                ))

        return sorted(modes, key=lambda m: m.start_position)

    def _find_missing_modes(self, detected: list) -> list[str]:
        """Identify which prescribed modes are missing from output."""
        detected_names = {m.mode for m in detected}
        prescribed = {m.value for m in ProtocolMode.prescribed_order()}
        return sorted(prescribed - detected_names)

    def _check_mode_order(self, detected: list) -> bool:
        """Check if detected modes follow prescribed order."""
        if not detected:
            return False
        prescribed = ProtocolMode.prescribed_order()
        prescribed_values = [m.value for m in prescribed]
        detected_values = [m.mode for m in detected]

        # Check that the order of detected modes matches their prescribed order
        filtered_prescribed = [m for m in prescribed_values if m in detected_values]
        return detected_values == filtered_prescribed

    # ─── Utility Methods ─────────────────────────────────────────────

    def _needs_sequential_loading(
        self, provider: InterpreterProvider, total_bytes: int, file_count: int
    ) -> bool:
        """Determine if corpus needs sequential loading for this provider."""
        # Rough heuristic: if total context exceeds ~60% of window, use sequential
        # This is conservative and can be tuned
        estimated_tokens = total_bytes // 4  # ~4 bytes per token estimate
        max_tokens = provider.max_context_tokens()
        return estimated_tokens > (max_tokens * 0.6)

    @staticmethod
    def _guess_mime_type(filename: str) -> str:
        """Guess MIME type from filename extension."""
        ext = Path(filename).suffix.lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".md": "text/markdown",
            ".txt": "text/plain",
            ".py": "text/x-python",
            ".js": "text/javascript",
            ".json": "application/json",
            ".html": "text/html",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
        }
        return mime_map.get(ext, "application/octet-stream")

    def _save_session(self, session: VerificationSession) -> None:
        """Save session state to disk."""
        session_dir = self.sessions_dir / session.session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        session_path = session_dir / "session.json"
        session_path.write_text(
            session.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _save_artifact(
        self, session: VerificationSession, run: InterpreterRun
    ) -> None:
        """Save interpreter output as immutable artifact."""
        if not run.response:
            return

        artifact_dir = (
            self.sessions_dir
            / session.session_id
            / "runs"
            / run.run_id
        )
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Save raw response (immutable)
        (artifact_dir / "response_raw.txt").write_text(
            run.response.raw_text, encoding="utf-8"
        )

        # Save metadata
        metadata = {
            "run_id": run.run_id,
            "session_type": session.session_type.value,
            "provider": run.interpreter.provider,
            "model": run.interpreter.model,
            "display_name": run.interpreter.display_name,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "prompt_hash": run.prompt_hash,
            "token_count_input": run.response.token_count_input,
            "token_count_output": run.response.token_count_output,
            "modes_detected": [m.mode for m in run.response.detected_modes],
            "modes_missing": run.response.missing_modes,
            "modes_in_order": run.response.modes_in_order,
            "corpus_loading_log": run.corpus_loading_log,
        }
        (artifact_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_session(self, session_id: str) -> VerificationSession:
        """Load session from disk."""
        session_path = self.sessions_dir / session_id / "session.json"
        if not session_path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        data = json.loads(session_path.read_text(encoding="utf-8"))
        return VerificationSession(**data)

    def list_sessions(self) -> list[dict]:
        """List all sessions with summary info."""
        sessions = []
        for session_dir in sorted(self.sessions_dir.iterdir()):
            session_path = session_dir / "session.json"
            if session_path.exists():
                try:
                    data = json.loads(session_path.read_text(encoding="utf-8"))
                    sessions.append({
                        "session_id": data["session_id"],
                        "created_at": data["created_at"],
                        "state": data["state"],
                        "session_type": data.get("session_type", "strict_verifier"),
                        "purpose": data["passport"]["purpose"],
                        "run_count": len(data.get("runs", [])),
                    })
                except Exception:
                    continue
        return sessions
