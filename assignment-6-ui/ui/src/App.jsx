import { useState } from "react";
import CommandBar from "./components/CommandBar";
import ActivityLog from "./components/ActivityLog";
import ProfileSettings from "./components/ProfileSettings";
import { useTaskSocket } from "./hooks/useTaskSocket";
import { sendCommand } from "./api";

export default function App() {
  const [tab, setTab] = useState("agent"); // "agent" | "profile"
  const [taskId, setTaskId] = useState(null);
  const [command, setCommand] = useState("");
  const [error, setError] = useState(null);

  const { messages, status } = useTaskSocket(taskId);
  const running = status === "running" || status === "connecting";

  async function onSubmit(cmd) {
    setError(null);
    setCommand(cmd);
    try {
      const { task_id } = await sendCommand(cmd);
      setTaskId(task_id); // opens the WebSocket via the hook
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <header className="mb-6">
        <h1 className="text-xl font-bold text-slate-900">🤖 AI Browser Agent</h1>
        <p className="text-sm text-slate-500">Type a command; watch the agent work in real time.</p>
      </header>

      <nav className="mb-6 flex gap-2">
        {["agent", "profile"].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-lg px-4 py-2 text-sm font-medium capitalize ${
              tab === t ? "bg-slate-900 text-white" : "bg-white text-slate-600 border border-slate-200"
            }`}
          >
            {t}
          </button>
        ))}
      </nav>

      {tab === "agent" ? (
        <div className="space-y-4">
          <CommandBar onSubmit={onSubmit} disabled={running} />
          {error && <p className="text-sm text-rose-600">{error}</p>}
          <ActivityLog command={command} messages={messages} status={status} />
        </div>
      ) : (
        <ProfileSettings />
      )}

      <footer className="mt-8 text-center text-xs text-slate-400">
        Backend: FastAPI · WebSocket live updates · Assignment 6
      </footer>
    </div>
  );
}
