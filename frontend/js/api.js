// api.js — shared helper for talking to the Mithra backend.
const API_BASE = "http://localhost:4000/api";

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

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}
