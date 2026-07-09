import { CalendarPlus, Check, X } from "lucide-react";
import Button from "./ui/Button";

// Proactive yes/no (e.g. "add this deadline to your calendar?").
export default function ConfirmPanel({ prompt, onResume }) {
  return (
    <div className="animate-fade-up flex items-center gap-4 rounded-2xl border border-indigo-200 bg-white p-4 shadow-soft">
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
        <CalendarPlus size={18} />
      </span>
      <p className="flex-1 text-sm font-medium text-ink">{prompt.question || "Proceed?"}</p>
      <div className="flex gap-2">
        <Button size="sm" onClick={() => onResume("approve")}>
          <Check size={15} /> Yes
        </Button>
        <Button size="sm" variant="secondary" onClick={() => onResume("reject")}>
          <X size={15} /> No
        </Button>
      </div>
    </div>
  );
}
