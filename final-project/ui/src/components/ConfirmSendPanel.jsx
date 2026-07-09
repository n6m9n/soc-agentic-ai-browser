import { useState } from "react";
import { Send, X, Mail } from "lucide-react";
import Button from "./ui/Button";

// Confirm-before-send (Module 2).
export default function ConfirmSendPanel({ prompt, onResume }) {
  const [draft, setDraft] = useState(prompt.draft);
  const set = (k, v) => setDraft((d) => ({ ...d, [k]: v }));
  const field = "h-10 w-full rounded-xl border border-line px-3 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/30";

  return (
    <div className="animate-fade-up overflow-hidden rounded-2xl border border-amber-200 bg-white shadow-soft">
      <div className="flex items-center gap-2.5 border-b border-amber-100 bg-amber-50/70 px-5 py-3.5">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-amber-100 text-amber-600">
          <Mail size={16} />
        </span>
        <div>
          <p className="text-sm font-semibold text-ink">Confirm before sending</p>
          <p className="text-xs text-muted">The agent never sends without your click.</p>
        </div>
      </div>
      <div className="space-y-3 px-5 py-4">
        <label className="block text-xs font-medium text-muted">To
          <input className={`mt-1 ${field}`} value={(draft.to || []).join(", ")}
            onChange={(e) => set("to", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))} />
        </label>
        <label className="block text-xs font-medium text-muted">Subject
          <input className={`mt-1 ${field}`} value={draft.subject || ""} onChange={(e) => set("subject", e.target.value)} />
        </label>
        <label className="block text-xs font-medium text-muted">Body
          <textarea rows={6} className="mt-1 w-full resize-none rounded-xl border border-line px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/30"
            value={draft.body || ""} onChange={(e) => set("body", e.target.value)} />
        </label>
      </div>
      <div className="flex gap-2 border-t border-line px-5 py-3.5">
        <Button size="sm" onClick={() => onResume("send", { draft })}>
          <Send size={15} /> Send email
        </Button>
        <Button size="sm" variant="secondary" onClick={() => onResume("reject")}>
          <X size={15} /> Cancel
        </Button>
      </div>
    </div>
  );
}
