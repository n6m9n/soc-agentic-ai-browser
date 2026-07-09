export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
export const WS_BASE = API_BASE.replace(/^http/, "ws");

async function json(res) {
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const sendCommand = (command) =>
  fetch(`${API_BASE}/command`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command }),
  }).then(json);

export const resumeTask = (taskId, decision, payload = {}) =>
  fetch(`${API_BASE}/command/${taskId}/resume`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, payload }),
  }).then(json);

export const getProfile = () => fetch(`${API_BASE}/user/profile`).then(json);

export const saveProfile = (profile) =>
  fetch(`${API_BASE}/user/profile`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  }).then(json);

export const getHistory = () => fetch(`${API_BASE}/memory/history`).then(json);

export const uploadDocument = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return fetch(`${API_BASE}/memory/resume`, { method: "POST", body: fd }).then(json);
};

export const googleStatus = () => fetch(`${API_BASE}/auth/google/status`).then(json);
