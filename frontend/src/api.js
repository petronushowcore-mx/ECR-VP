/**
 * ECR-VP API Client
 *
 * Connects the React frontend to the FastAPI backend.
 * All calls go through /api/* which Vite proxies to localhost:8000
 * in development, and which is served directly in production.
 */

const BASE = "/api";

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

// ─── Health ──────────────────────────────────────────────────────────────

export async function getHealth() {
  return request("/health");
}

// ─── Files ───────────────────────────────────────────────────────────────

export async function uploadFiles(fileList) {
  const form = new FormData();
  for (const file of fileList) {
    form.append("files", file);
  }
  const res = await fetch(`${BASE}/files/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Upload error ${res.status}`);
  }
  return res.json();
}

export async function listFiles() {
  return request("/files");
}

export async function deleteFile(fileId) {
  return request(`/files/${encodeURIComponent(fileId)}`, { method: "DELETE" });
}

// ─── Passports ───────────────────────────────────────────────────────────

export async function createPassport({
  purpose,
  architecturalStatus,
  canonVersion,
  constraints,
  fileIds,
}) {
  return request("/passports", {
    method: "POST",
    body: JSON.stringify({
      purpose,
      architectural_status: architecturalStatus,
      canon_version: canonVersion,
      constraints: constraints || [],
      file_ids: fileIds,
    }),
  });
}

export async function listPassports() {
  return request("/passports");
}

export async function getPassport(passportId) {
  return request(`/passports/${passportId}`);
}

export async function verifyPassportIntegrity(passportId) {
  return request(`/passports/${passportId}/verify`);
}

// ─── Sessions ────────────────────────────────────────────────────────────

export async function createSession({ passportId, interpreters }) {
  return request("/sessions", {
    method: "POST",
    body: JSON.stringify({
      passport_id: passportId,
      interpreters: interpreters.map((i) => ({
        provider: i.provider,
        model: i.model,
        display_name: i.displayName || `${i.provider}/${i.model}`,
        api_key_env: i.apiKeyEnv || null,
        base_url: i.baseUrl || null,
        max_tokens: i.maxTokens || 16384,
        temperature: i.temperature ?? 0.0,
      })),
    }),
  });
}

export async function executeSession(sessionId, { parallel = true } = {}) {
  return request(`/sessions/${sessionId}/execute`, {
    method: "POST",
    body: JSON.stringify({ parallel }),
  });
}

export async function listSessions() {
  return request("/sessions");
}

export async function getSession(sessionId) {
  return request(`/sessions/${sessionId}`);
}

export async function getRunResponse(sessionId, runId) {
  return request(`/sessions/${sessionId}/runs/${runId}/response`);
}

// ─── Providers ───────────────────────────────────────────────────────────

export async function listProviders() {
  return request("/providers");
}
