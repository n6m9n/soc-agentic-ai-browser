import { useEffect, useState } from "react";
import { getProfile, saveProfile } from "../api";

const FIELDS = [
  ["name", "Name", "input"],
  ["email", "Email", "input"],
  ["phone", "Phone", "input"],
  ["address", "Address", "input"],
  ["resume_text", "Resume text", "textarea"],
];

// User profile settings page — reads/writes the agent's memory via the backend.
export default function ProfileSettings() {
  const [profile, setProfile] = useState({
    name: "", email: "", phone: "", address: "", resume_text: "",
  });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getProfile().then(setProfile).catch((e) => setError(e.message));
  }, []);

  function update(key, value) {
    setProfile((p) => ({ ...p, [key]: value }));
    setSaved(false);
  }

  async function onSave(e) {
    e.preventDefault();
    setError(null);
    try {
      const updated = await saveProfile(profile);
      setProfile(updated);
      setSaved(true);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <form onSubmit={onSave} className="rounded-xl border border-slate-200 bg-white p-4">
      <h2 className="mb-4 text-sm font-semibold text-slate-700">Profile (agent memory)</h2>
      <div className="space-y-3">
        {FIELDS.map(([key, label, kind]) => (
          <label key={key} className="block">
            <span className="mb-1 block text-xs font-medium text-slate-500">{label}</span>
            {kind === "textarea" ? (
              <textarea
                rows={4}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={profile[key] || ""}
                onChange={(e) => update(key, e.target.value)}
              />
            ) : (
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={profile[key] || ""}
                onChange={(e) => update(key, e.target.value)}
              />
            )}
          </label>
        ))}
      </div>

      <div className="mt-4 flex items-center gap-3">
        <button
          type="submit"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Save
        </button>
        {saved && <span className="text-xs text-emerald-600">Saved ✓</span>}
        {error && <span className="text-xs text-rose-600">{error}</span>}
      </div>
    </form>
  );
}
