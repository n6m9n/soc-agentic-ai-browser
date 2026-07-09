// Live activity feed: one row per agent step streamed over the WebSocket.
const DOT = {
  running: "bg-amber-400",
  completed: "bg-emerald-500",
  failed: "bg-rose-500",
};

export default function ActivityLog({ command, messages, status }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">Activity</h2>
        {status && (
          <span className="flex items-center gap-2 text-xs text-slate-500">
            <span className={`h-2 w-2 rounded-full ${DOT[status] || "bg-slate-300"}`} />
            {status}
          </span>
        )}
      </div>

      {command && (
        <p className="mb-3 rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-600">
          <span className="font-medium">Command:</span> {command}
        </p>
      )}

      {messages.length === 0 ? (
        <p className="text-sm text-slate-400">No steps yet — run a command above.</p>
      ) : (
        <ol className="space-y-2">
          {messages.map((m, i) => (
            <li key={i} className="flex gap-3 text-sm">
              <span className="mt-0.5 w-5 shrink-0 text-right text-xs text-slate-400">
                {i + 1}
              </span>
              <span className="text-slate-700">{m.message}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
