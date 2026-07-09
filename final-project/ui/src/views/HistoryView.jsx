import { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import Card from "../components/ui/Card";
import { ActivityItem, ActivityEmpty } from "../components/Activity";
import { getHistory } from "../api";

export default function HistoryView() {
  const [rows, setRows] = useState([]);
  const [err, setErr] = useState("");
  useEffect(() => { getHistory().then(setRows).catch((e) => setErr(e.message)); }, []);

  const items = rows.map((r) => ({
    title: r.command,
    meta: `${r.status}${r.result ? " · " + r.result : ""}`,
    state: r.status === "failed" ? "failed" : "done",
  }));

  return (
    <div className="space-y-5">
      <header className="flex items-center gap-3">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary"><Clock size={18} /></span>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-ink">Task history</h1>
          <p className="text-sm text-muted">Every command your assistant has run.</p>
        </div>
      </header>
      <Card className="p-6">
        {err && <p className="text-sm text-rose-600">{err}</p>}
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
    </div>
  );
}
