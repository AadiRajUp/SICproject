const API_BASE =
  process.env.REACT_APP_API_BASE_URL?.replace(/\/+$/, "") ||
  "http://localhost:5000";

async function parseJson(res) {
  const text = await res.text();
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
}

export async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
  const res = await fetch(url, {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const body = await parseJson(res);
  if (!res.ok) {
    const message = body?.error || body?.message || `Request failed (${res.status})`;
    const err = new Error(message);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

