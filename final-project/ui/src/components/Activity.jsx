import { Check, X, Loader2, Sparkles } from "lucide-react";

const STATE_STYLES = {
  running: { ring: "border-amber-200 bg-amber-50 text-amber-500", icon: <Loader2 size={15} className="animate-spin" /> },
  failed: { ring: "border-rose-200 bg-rose-50 text-rose-500", icon: <X size={15} /> },
  done: { ring: "border-emerald-200 bg-emerald-50 text-emerald-600", icon: <Check size={15} /> },
};

export function ActivityItem({ title, meta, state = "done", last = false }) {
  const s = STATE_STYLES[state] || STATE_STYLES.done;
  return (
    <li className="relative flex gap-4 animate-fade-up">
      <div className="flex flex-col items-center">
        <span className={`grid h-8 w-8 place-items-center rounded-full border ${s.ring}`}>{s.icon}</span>
        {!last && <span className="mt-1 w-px flex-1 bg-line" />}
      </div>
      <div className={last ? "pb-0" : "pb-6"}>
        <p className="text-sm font-medium leading-snug text-ink">{title}</p>
        {meta && <p className="mt-0.5 text-xs text-muted">{meta}</p>}
      </div>
    </li>
  );
}

export function ActivityEmpty() {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
      <div className="relative mb-5">
        <div className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-indigo-50 to-violet-50">
          <Sparkles size={26} className="text-primary" />
        </div>
        <div className="absolute -inset-2 -z-10 rounded-3xl bg-primary/5 blur-xl" />
      </div>
      <p className="text-sm font-semibold text-ink">No activity yet</p>
      <p className="mt-1 max-w-[220px] text-xs leading-relaxed text-muted">
        Run your first command and each step will appear here in real time.
      </p>
    </div>
  );
}
