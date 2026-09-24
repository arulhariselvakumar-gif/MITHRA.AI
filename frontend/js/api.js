// api.js — shared helper for talking to the Mithra backend.

// Check if an api_url was provided in the query string (e.g. ?api_url=https://...)
(function checkQueryParamApiUrl() {
  if (typeof window !== "undefined" && window.location && window.location.search) {
    try {
      const params = new URLSearchParams(window.location.search);
      const urlFromQuery = params.get("api_url") || params.get("api");
      if (urlFromQuery) {
        localStorage.setItem("mithra_api_url", urlFromQuery.trim().replace(/\/+$/, ""));
      }
    } catch (_) {}
  }
})();

/**
 * Returns the base backend origin (e.g. "http://localhost:4000" or "https://api.yourdomain.com").
 * Order of precedence:
 * 1. window.MITHRA_CONFIG.API_URL (set via Netlify MITHRA_API_URL or config.js)
 * 2. window.__MITHRA_API_URL__ (global variable)
 * 3. localStorage.getItem("mithra_api_url") (browser setting / testing override)
 * 4. Localhost / 127.0.0.1 default: "http://localhost:4000"
 * 5. Deployed default when unconfigured: "" (relative / not configured)
 */
function getBackendUrl() {
  if (typeof window !== "undefined" && window.MITHRA_CONFIG && window.MITHRA_CONFIG.API_URL) {
    const u = String(window.MITHRA_CONFIG.API_URL).trim();
    if (u) return u.replace(/\/+$/, "");
  }
  if (typeof window !== "undefined" && window.__MITHRA_API_URL__) {
    const u = String(window.__MITHRA_API_URL__).trim();
    if (u) return u.replace(/\/+$/, "");
  }
  if (typeof localStorage !== "undefined") {
    const stored = localStorage.getItem("mithra_api_url");
    if (stored && stored.trim()) {
      return stored.trim().replace(/\/+$/, "");
    }
  }
  if (typeof window !== "undefined" && window.location) {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1" || host === "0.0.0.0") {
      return "http://localhost:4000";
    }
  }
  return "";
}

/**
 * Returns the full API base URL (e.g. "http://localhost:4000/api" or "https://api.yourdomain.com/api").
 */
function getApiBase() {
  const backend = getBackendUrl();
  return backend ? `${backend}/api` : "/api";
}

const API_BASE = getApiBase();

function getToken() {
  return localStorage.getItem("mithra_token");
}
function setSession(token, user) {
  localStorage.setItem("mithra_token", token);
  localStorage.setItem("mithra_user", JSON.stringify(user));
}
function getUser() {
  try { return JSON.parse(localStorage.getItem("mithra_user")); } catch { return null; }
}
function logout() {
  localStorage.removeItem("mithra_token");
  localStorage.removeItem("mithra_user");
  window.location.href = "login.html";
}
function requireLogin() {
  if (!getToken()) window.location.href = "login.html";
}

async function api(path, { method = "GET", body, isForm = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isForm) headers["Content-Type"] = "application/json";

  const baseUrl = getApiBase();
  const res = await fetch(`${baseUrl}${path}`, {
    method,
    headers,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}
