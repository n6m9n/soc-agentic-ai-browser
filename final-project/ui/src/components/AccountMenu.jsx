import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { API_BASE, googleStatus, getProfile } from "../api";

function initials(name) {
  if (!name) return "N";
  return name.split(" ").map((s) => s[0]).slice(0, 2).join("").toUpperCase();
}

export default function AccountMenu() {
  const [status, setStatus] = useState(null);
  const [name, setName] = useState("");

  useEffect(() => {
    googleStatus().then(setStatus).catch(() => {});
    getProfile().then((p) => setName(p.name || "")).catch(() => {});
  }, []);

  const connected = status?.connected;
  return (
    <div className="flex items-center gap-3">
      {connected ? (
        <span className="hidden items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 sm:inline-flex">
          <Check size={13} /> Google connected
        </span>
      ) : (
        <a
          href={`${API_BASE}/auth/google/login`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 rounded-full border border-line bg-white px-3.5 py-1.5 text-xs font-semibold text-ink shadow-soft transition-all hover:-translate-y-0.5 hover:shadow-lift"
        >
          <GoogleGlyph /> Connect Google
        </a>
      )}
      <button className="grid h-9 w-9 place-items-center rounded-full gradient-primary text-xs font-bold text-white shadow-glow">
        {initials(name)}
      </button>
    </div>
  );
}

function GoogleGlyph() {
  return (
    <svg width="14" height="14" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.6l6.7-6.7C35.6 2.4 30.1 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.8 6.1C12.3 13.2 17.6 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.1 24.6c0-1.6-.1-3.2-.4-4.6H24v9.1h12.4c-.5 2.9-2.1 5.3-4.6 7l7.1 5.5c4.2-3.9 6.6-9.6 6.6-16.9z" />
      <path fill="#FBBC05" d="M10.4 28.3a14.5 14.5 0 0 1 0-8.6l-7.8-6.1a24 24 0 0 0 0 20.8l7.8-6.1z" />
      <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.1-5.5c-2 1.4-4.6 2.2-8.8 2.2-6.4 0-11.7-3.7-13.6-9.1l-7.8 6.1C6.5 42.6 14.6 48 24 48z" />
    </svg>
  );
}
