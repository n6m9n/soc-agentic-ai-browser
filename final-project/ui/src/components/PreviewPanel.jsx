import { useState } from "react";
import { ClipboardCheck, Check, X } from "lucide-react";
import Button from "./ui/Button";

// Review-before-submit (Module 1).
export default function PreviewPanel({ prompt, onResume }) {
  const [values, setValues] = useState(() =>
    Object.fromEntries(prompt.previews.map((p) => [p.selector, p.value || ""]))
  );
  const set = (sel, v) => setValues((s) => ({ ...s, [sel]: v }));

  return (
    <div className="animate-fade-up overflow-hidden rounded-2xl border border-sky-200 bg-white shadow-soft">
      <div className="flex items-center gap-2.5 border-b border-sky-100 bg-sky-50/70 px-5 py-3.5">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-sky-100 text-sky-600">
          <ClipboardCheck size={16} />
        </span>
        <div>
          <p className="text-sm font-semibold text-ink">Review before submitting</p>
          <p className="text-xs text-muted">Edit any field, then approve.</p>
        </div>
      </div>
      <div className="space-y-2.5 px-5 py-4">
        {prompt.previews.map((p) => (
          <div key={p.selector} className="grid grid-cols-3 items-center gap-3">
            <label className="truncate text-xs font-medium text-muted" title={p.field}>
              {p.field || p.selector}
              {p.needs_user && <span className="ml-1 text-rose-500">• needed</span>}
            </label>
            <input
              className={`col-span-2 h-10 rounded-xl border px-3 text-sm text-ink transition-all focus:outline-none focus:ring-2 focus:ring-primary/30
                ${p.needs_user ? "border-rose-200 bg-rose-50/40" : "border-line bg-white"}`}
              value={values[p.selector]}
              onChange={(e) => set(p.selector, e.target.value)}
            />
          </div>
        ))}
      </div>
      <div className="flex gap-2 border-t border-line px-5 py-3.5">
        <Button size="sm" onClick={() => onResume("approve", { values })}>
          <Check size={15} /> Approve &amp; submit
        </Button>
        <Button size="sm" variant="secondary" onClick={() => onResume("reject")}>
          <X size={15} /> Reject
        </Button>
      </div>
    </div>
  );
}
