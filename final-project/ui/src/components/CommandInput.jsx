import { useRef, useState } from "react";
import { ArrowUp, Sparkles, Paperclip, Loader2, FileText, X, Check } from "lucide-react";
import Button from "./ui/Button";
import { uploadDocument } from "../api";

export default function CommandInput({ value, onChange, onSubmit, disabled }) {
  const ref = useRef(null);
  const fileRef = useRef(null);
  const [attached, setAttached] = useState(null); // { name, chunks }
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  function grow(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 220) + "px";
  }
  function onKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) onSubmit();
    }
  }

  async function onFile(e) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-selecting the same file
    if (!file) return;
    setErr("");
    setBusy(true);
    try {
      const res = await uploadDocument(file);
      setAttached({ name: file.name, chunks: res.chunks_stored });
    } catch (e2) {
      setErr("Upload failed — is the backend running? PDFs only.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="group relative rounded-3xl border border-line bg-white p-2 shadow-soft transition-all duration-200 focus-within:border-primary/40 focus-within:shadow-glow">
        <div className="flex items-start gap-3 px-3 pt-3">
          <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-xl gradient-primary text-white shadow-glow">
            <Sparkles size={16} />
          </div>
          <textarea
            ref={ref}
            rows={1}
            value={value}
            disabled={disabled}
            onChange={(e) => { onChange(e.target.value); grow(e.target); }}
            onKeyDown={onKey}
            placeholder="Ask me to summarize a page, draft an email, fill a form, schedule a meeting…"
            className="max-h-[220px] min-h-[28px] w-full resize-none bg-transparent py-1 text-[15px] leading-6 text-ink placeholder:text-slate-400 focus:outline-none"
          />
        </div>

        {attached && (
          <div className="mx-3 mb-1 mt-2 inline-flex items-center gap-2 rounded-lg border border-line bg-slate-50 px-2.5 py-1.5 text-xs text-ink">
            <FileText size={14} className="text-primary" />
            <span className="max-w-[220px] truncate font-medium">{attached.name}</span>
            <span className="text-muted">· added to memory</span>
            <Check size={13} className="text-emerald-600" />
            <button onClick={() => setAttached(null)} className="ml-1 text-slate-400 hover:text-ink">
              <X size={13} />
            </button>
          </div>
        )}

        <div className="flex items-center justify-between px-2 pb-1.5 pt-2">
          <div className="flex items-center gap-2 text-xs text-muted">
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              disabled={busy}
              className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-ink disabled:opacity-50"
              title="Attach a PDF (added to the agent's memory)"
            >
              {busy ? <Loader2 size={15} className="animate-spin" /> : <Paperclip size={15} />}
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={onFile}
            />
            <span className="hidden sm:inline">
              <kbd>⏎</kbd> to run · <kbd>⇧⏎</kbd> new line
            </span>
          </div>
          <Button size="sm" onClick={onSubmit} disabled={disabled || !value.trim()} className="rounded-xl">
            Run <ArrowUp size={16} />
          </Button>
        </div>
      </div>
      {err && <p className="mt-2 px-2 text-xs text-rose-600">{err}</p>}
    </div>
  );
}
