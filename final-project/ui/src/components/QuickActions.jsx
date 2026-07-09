import { FileText, Mail, CalendarDays, ClipboardList, Globe } from "lucide-react";

const ACTIONS = [
  { icon: FileText, label: "Summarize Page", hint: "Any URL or PDF", cmd: "Summarize " },
  { icon: Mail, label: "Draft Email", hint: "From one line", cmd: "Email my mentor that " },
  { icon: CalendarDays, label: "Manage Calendar", hint: "Slots & events", cmd: "Add a study block every evening this week" },
  { icon: ClipboardList, label: "Fill Form", hint: "Autofill memory", cmd: "Fill this form: " },
  { icon: Globe, label: "Research Topic", hint: "Compare sources", cmd: "Research " },
];

export default function QuickActions({ onPick }) {
  return (
    <div className="grid grid-cols-2 gap-3 stagger sm:grid-cols-3 lg:grid-cols-5">
      {ACTIONS.map(({ icon: Icon, label, hint, cmd }) => (
        <button
          key={label}
          onClick={() => onPick(cmd)}
          className="group flex flex-col items-start gap-3 rounded-2xl border border-line bg-white p-4 text-left shadow-soft transition-all duration-200 hover:-translate-y-1 hover:border-slate-300 hover:shadow-lift"
        >
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary transition-all duration-200 group-hover:gradient-primary group-hover:text-white group-hover:shadow-glow">
            <Icon size={19} />
          </span>
          <span className="text-[13px] font-semibold leading-tight text-ink">{label}</span>
          <span className="-mt-1.5 text-[11px] text-muted">{hint}</span>
        </button>
      ))}
    </div>
  );
}
