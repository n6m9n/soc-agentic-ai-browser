import CommandInput from "../components/CommandInput";
import QuickActions from "../components/QuickActions";
import Card from "../components/ui/Card";
import { ActivityItem, ActivityEmpty } from "../components/Activity";
import PreviewPanel from "../components/PreviewPanel";
import ConfirmSendPanel from "../components/ConfirmSendPanel";
import ConfirmPanel from "../components/ConfirmPanel";

const EXAMPLES = [
  "Summarize this webpage",
  "Reply to my emails",
  "Fill this form",
  "Schedule a meeting",
];

const RUNNING = ["running", "connecting", "needs_input"];

function Hitl({ prompt, onResume }) {
  if (prompt.type === "preview") return <PreviewPanel prompt={prompt} onResume={onResume} />;
  if (prompt.type === "confirm_send") return <ConfirmSendPanel prompt={prompt} onResume={onResume} />;
  return <ConfirmPanel prompt={prompt} onResume={onResume} />;
}

export default function AgentView({
  name, value, setValue, onRun, running, messages, status, prompt, onResume, history,
}) {
  const liveItems = messages.map((m, i) => ({
    title: m.message,
    state:
      i === messages.length - 1
        ? status === "failed" ? "failed" : RUNNING.includes(status) ? "running" : "done"
        : "done",
  }));

  const historyItems = (history || []).slice(0, 6).map((r) => ({
    title: r.command,
    meta: r.status === "completed" ? "Completed" : r.status,
    state: r.status === "failed" ? "failed" : "done",
  }));

  const showLive = messages.length > 0;
  const items = showLive ? liveItems : historyItems;

  return (
    <div className="space-y-10">
      {/* Hero */}
      <section className="animate-fade-up pt-2">
        <h1 className="text-[28px] font-bold leading-tight tracking-tight text-ink sm:text-[34px]">
          <span className="mr-1">👋</span> Welcome back, <span className="gradient-text">{name || "there"}</span>
        </h1>
        <p className="mt-2 text-[15px] text-muted">What would you like me to do today?</p>

        <div className="mt-6">
          <CommandInput value={value} onChange={setValue} onSubmit={onRun} disabled={running} />
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setValue(ex)}
              className="rounded-full border border-line bg-white px-3.5 py-1.5 text-xs font-medium text-muted shadow-soft transition-all hover:-translate-y-0.5 hover:text-ink hover:shadow-lift"
            >
              {ex}
            </button>
          ))}
        </div>
      </section>

      {/* Quick actions */}
      <section>
        <SectionTitle title="Quick actions" subtitle="One tap to prefill a command" />
        <QuickActions onPick={(cmd) => setValue(cmd)} />
      </section>

      {/* Human-in-the-loop */}
      {prompt && status === "needs_input" && (
        <section><Hitl prompt={prompt} onResume={onResume} /></section>
      )}

      {/* Activity */}
      <section>
        <SectionTitle
          title={showLive ? "Live activity" : "Recent activity"}
          subtitle={showLive ? "Streaming each step in real time" : "Your latest runs"}
          status={showLive ? status : null}
        />
        <Card className="p-5">
          {items.length === 0 ? (
            <ActivityEmpty />
          ) : (
            <ul className="pt-1">
              {items.map((it, i) => (
                <ActivityItem key={i} {...it} last={i === items.length - 1} />
              ))}
            </ul>
          )}
        </Card>
      </section>
    </div>
  );
}

function SectionTitle({ title, subtitle, status }) {
  return (
    <div className="mb-4 flex items-end justify-between">
      <div>
        <h2 className="text-[15px] font-semibold text-ink">{title}</h2>
        {subtitle && <p className="text-xs text-muted">{subtitle}</p>}
      </div>
      {status && (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-muted">
          <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-amber-400" /> {status}
        </span>
      )}
    </div>
  );
}
