// Backend base URL. Override with VITE_API_BASE if the API runs elsewhere.
export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
export const WS_BASE = API_BASE.replace(/^http/, "ws");

export async function sendCommand(command) {
  const res = await fetch(`${API_BASE}/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command }),
  });
  if (!res.ok) throw new Error(`command failed: ${res.status}`);
  return res.json(); // { task_id, status }
}

export async function getProfile() {
  const res = await fetch(`${API_BASE}/user/profile`);
  if (!res.ok) throw new Error(`getProfile failed: ${res.status}`);
  return res.json();
}

export async function saveProfile(profile) {
  const res = await fetch(`${API_BASE}/user/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error(`saveProfile failed: ${res.status}`);
  return res.json();
}
