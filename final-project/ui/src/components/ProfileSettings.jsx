import { useEffect, useState } from "react";
import { Save, UploadCloud, Database, BadgeCheck } from "lucide-react";
import Button from "./ui/Button";
import Card from "./ui/Card";
import { getProfile, saveProfile, API_BASE } from "../api";

const FIELDS = [
  ["name", "Full name"], ["email", "Email"], ["phone", "Phone"],
  ["college", "College"], ["degree", "Degree"], ["grad_year", "Graduation year"],
  ["city", "City"], ["linkedin", "LinkedIn"],
];

export default function ProfileSettings() {
  const [profile, setProfile] = useState({});
  const [saved, setSaved] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => { getProfile().then(setProfile).catch((e) => setMsg(e.message)); }, []);
  const set = (k, v) => { setProfile((p) => ({ ...p, [k]: v })); setSaved(false); };

  async function onSave(e) {
    e.preventDefault();
    try { setProfile(await saveProfile(profile)); setSaved(true); }
    catch (e) { setMsg(e.message); }
  }
  async function ingest() {
    const r = await fetch(`${API_BASE}/memory/ingest-profile`, { method: "POST" });
    setMsg(r.ok ? "Profile embedded into memory ✓" : "Set GOOGLE_API_KEY to embed");
  }
  async function uploadResume(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData(); fd.append("file", file);
    const r = await fetch(`${API_BASE}/memory/resume`, { method: "POST", body: fd });
    setMsg(r.ok ? "Resume parsed into memory ✓" : "Resume upload failed");
  }

  return (
    <form onSubmit={onSave} className="space-y-5">
      <Card className="p-6">
        <h2 className="text-base font-semibold text-ink">Profile</h2>
        <p className="mt-1 text-sm text-muted">The memory your assistant fills forms and writes emails from.</p>
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {FIELDS.map(([k, label]) => (
            <label key={k} className="block">
              <span className="mb-1.5 block text-xs font-semibold text-muted">{label}</span>
              <input
                className="h-11 w-full rounded-xl border border-line bg-white px-3.5 text-sm text-ink transition-all focus:outline-none focus:ring-2 focus:ring-primary/30"
                value={profile[k] || ""}
                onChange={(e) => set(k, e.target.value)}
              />
            </label>
          ))}
        </div>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Button type="submit"><Save size={16} /> Save profile</Button>
          {saved && (
            <span className="inline-flex items-center gap-1 text-sm font-medium text-emerald-600">
              <BadgeCheck size={16} /> Saved
            </span>
          )}
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-base font-semibold text-ink">Memory &amp; documents</h3>
        <p className="mt-1 text-sm text-muted">Embed your profile and resume so cRAG can recall them.</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Button type="button" variant="secondary" onClick={ingest}>
            <Database size={16} /> Embed profile
          </Button>
          <label className="inline-flex h-12 cursor-pointer items-center gap-2 rounded-xl border border-line bg-white px-5 text-sm font-semibold text-ink shadow-soft transition-all hover:-translate-y-0.5 hover:shadow-lift">
            <UploadCloud size={16} /> Upload resume PDF
            <input type="file" accept="application/pdf" className="hidden" onChange={uploadResume} />
          </label>
        </div>
        {msg && <p className="mt-3 text-xs text-muted">{msg}</p>}
      </Card>
    </form>
  );
}
