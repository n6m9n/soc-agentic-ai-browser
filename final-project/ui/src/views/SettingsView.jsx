import { useEffect, useState } from "react";
import { Check, Cpu, Link2 } from "lucide-react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import { API_BASE, googleStatus } from "../api";

export default function SettingsView() {
  const [status, setStatus] = useState(null);
  useEffect(() => { googleStatus().then(setStatus).catch(() => {}); }, []);
  const connected = status?.connected;

  return (
    <div className="space-y-5">
      <header className="flex items-center gap-3">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary"><Link2 size={18} /></span>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-ink">Settings</h1>
          <p className="text-sm text-muted">Connected accounts and model.</p>
        </div>
      </header>

      <Card className="p-6">
        <h2 className="text-base font-semibold text-ink">Connected accounts</h2>
        <div className="mt-4 flex items-center justify-between rounded-xl border border-line bg-slate-50/60 p-4">
          <div className="flex items-center gap-3">
            <GoogleGlyph />
            <div>
              <p className="text-sm font-semibold text-ink">Google — Gmail &amp; Calendar</p>
              <p className="text-xs text-muted">Send email, schedule events, find free slots.</p>
            </div>
          </div>
          {connected ? (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">
              <Check size={13} /> Connected
            </span>
          ) : (
            <a href={`${API_BASE}/auth/google/login`} target="_blank" rel="noreferrer">
              <Button size="sm" variant="secondary">Connect</Button>
            </a>
          )}
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary"><Cpu size={18} /></span>
          <div>
            <p className="text-sm font-semibold text-ink">Model</p>
            <p className="text-xs text-muted">Gemini · free tier · cRAG memory (ChromaDB embeddings)</p>
          </div>
        </div>
      </Card>
    </div>
  );
}

function GoogleGlyph() {
  return (
    <svg width="22" height="22" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.6l6.7-6.7C35.6 2.4 30.1 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.8 6.1C12.3 13.2 17.6 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.1 24.6c0-1.6-.1-3.2-.4-4.6H24v9.1h12.4c-.5 2.9-2.1 5.3-4.6 7l7.1 5.5c4.2-3.9 6.6-9.6 6.6-16.9z" />
      <path fill="#FBBC05" d="M10.4 28.3a14.5 14.5 0 0 1 0-8.6l-7.8-6.1a24 24 0 0 0 0 20.8l7.8-6.1z" />
      <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.1-5.5c-2 1.4-4.6 2.2-8.8 2.2-6.4 0-11.7-3.7-13.6-9.1l-7.8 6.1C6.5 42.6 14.6 48 24 48z" />
    </svg>
  );
}
