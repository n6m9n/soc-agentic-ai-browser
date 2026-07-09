import { Sparkles, MessageSquareText, History, User, Settings } from "lucide-react";

export const NAV = [
  { id: "agent", label: "Agent", icon: MessageSquareText },
  { id: "history", label: "History", icon: History },
  { id: "profile", label: "Profile", icon: User },
  { id: "settings", label: "Settings", icon: Settings },
];

function Logo() {
  return (
    <div className="flex items-center gap-3 px-2">
      <div className="grid h-9 w-9 place-items-center rounded-xl gradient-primary text-white shadow-glow">
        <Sparkles size={18} />
      </div>
      <div className="leading-tight">
        <p className="text-[15px] font-bold tracking-tight text-ink">Aria</p>
        <p className="text-[11px] font-medium text-muted">Browser Assistant</p>
      </div>
    </div>
  );
}

export default function Sidebar({ active, onSelect }) {
  return (
    <aside className="hidden w-[264px] shrink-0 flex-col border-r border-line bg-white/70 glass px-4 py-6 lg:flex">
      <Logo />
      <nav className="mt-8 flex flex-col gap-1">
        <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Workspace
        </p>
        {NAV.map(({ id, label, icon: Icon }) => {
          const on = active === id;
          return (
            <button
              key={id}
              onClick={() => onSelect(id)}
              className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200
                ${on ? "bg-slate-100 text-ink shadow-soft" : "text-muted hover:bg-slate-50 hover:text-ink"}`}
            >
              <Icon size={18} className={on ? "text-primary" : "text-slate-400 group-hover:text-ink"} />
              {label}
              {on && <span className="ml-auto h-1.5 w-1.5 rounded-full gradient-primary" />}
            </button>
          );
        })}
      </nav>

      <div className="mt-auto rounded-2xl border border-line bg-slate-50/80 p-4">
        <p className="text-xs font-semibold text-ink">Powered by Gemini</p>
        <p className="mt-1 text-[11px] leading-relaxed text-muted">
          cRAG memory · Playwright · Gmail &amp; Calendar
        </p>
      </div>
    </aside>
  );
}

export function BottomNav({ active, onSelect }) {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex justify-around border-t border-line glass py-2 lg:hidden">
      {NAV.map(({ id, label, icon: Icon }) => {
        const on = active === id;
        return (
          <button
            key={id}
            onClick={() => onSelect(id)}
            className={`flex w-16 flex-col items-center gap-1 rounded-lg py-1 text-[10px] font-medium transition-colors
              ${on ? "text-primary" : "text-muted"}`}
          >
            <Icon size={20} />
            {label}
          </button>
        );
      })}
    </nav>
  );
}
