// Auto-detect API URL based on environment
const API_BASE = (() => {
  // For production (deployed on Railway)
  if (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
    return window.location.protocol + "//" + window.location.host;
  }
  // For local development
  return "http://127.0.0.1:8000";
})();

// Or manually override: export const API_BASE = "https://your-railway-domain.railway.app";

const AUTH_STORAGE_KEY = "tridentwear-auth-session";

function resolveUrl(path) {
  if (/^https?:\/\//.test(path)) {
    return path;
  }
  if (path.startsWith("/")) {
    return `${API_BASE}${path}`;
  }
  return `${API_BASE}/${path}`;
}

export function resolveAssetUrl(path) {
  if (!path) {
    return `${API_BASE}/images/hero-banner.png`;
  }
  if (path.startsWith("data:") || /^https?:\/\//.test(path)) {
    return path;
  }
  if (path.startsWith("/")) {
    return `${API_BASE}${path}`;
  }
  return `${API_BASE}/${path}`;
}

export function getAuthSession() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveAuthSession(session) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  return session;
}

export function clearAuthSession() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const session = getAuthSession();
  const token = session?.token;

  if (token && !headers.has("authorization") && !headers.has("Authorization") && !headers.has("x-session-token")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(resolveUrl(path), {
    credentials: "same-origin",
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    const error = new Error(payload?.detail || payload?.message || "Request failed.");
    error.status = response.status;
    error.path = path;
    throw error;
  }

  return payload;
}

export async function requestWithFallback(paths, options = {}) {
  let lastError = null;

  for (const path of paths) {
    try {
      return await request(path, options);
    } catch (error) {
      lastError = error;
      if (error.status !== 404) {
        throw error;
      }
    }
  }

  throw lastError || new Error("Request failed.");
}

export function get(path) {
  return request(path);
}

export function getWithFallback(paths) {
  return requestWithFallback(paths);
}

export function post(path, body) {
  return request(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export function postWithFallback(paths, body) {
  return requestWithFallback(paths, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export function del(path) {
  return request(path, {
    method: "DELETE",
  });
}

export function postForm(path, formData) {
  return request(path, {
    method: "POST",
    body: formData,
  });
}

export function putForm(path, formData) {
  return request(path, {
    method: "PUT",
    body: formData,
  });
}
