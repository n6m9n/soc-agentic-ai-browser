import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import Sidebar, { BottomNav } from "./components/Sidebar";
import AccountMenu from "./components/AccountMenu";
import AgentView from "./views/AgentView";
import HistoryView from "./views/HistoryView";
import ProfileView from "./views/ProfileView";
import SettingsView from "./views/SettingsView";
import { useTaskSocket } from "./hooks/useTaskSocket";
import { sendCommand, resumeTask, getProfile, getHistory } from "./api";

const today = new Date().toLocaleDateString(undefined, {
  weekday: "long", month: "long", day: "numeric",
});

export default function App() {
  const [view, setView] = useState("agent");
  const [taskId, setTaskId] = useState(null);
  const [value, setValue] = useState("");
  const [name, setName] = useState("");
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

  const { messages, status, prompt, clearPrompt } = useTaskSocket(taskId);
  const running = ["connecting", "running", "needs_input"].includes(status);

  useEffect(() => {
    getProfile().then((p) => setName(p.name || "")).catch(() => {});
    getHistory().then(setHistory).catch(() => {});
  }, []);

  useEffect(() => {
    if (status === "completed" || status === "failed") getHistory().then(setHistory).catch(() => {});
  }, [status]);

  async function onRun() {
    const cmd = value.trim();
    if (!cmd) return;
    setError(null);
    try {
      const { task_id } = await sendCommand(cmd);
      setTaskId(task_id);
      setValue("");
    } catch (e) { setError(e.message); }
  }

  async function onResume(decision, payload = {}) {
    try { await resumeTask(taskId, decision, payload); clearPrompt(); }
    catch (e) { setError(e.message); }
  }

  return (
    <div className="app-bg flex min-h-screen">
      <Sidebar active={view} onSelect={setView} />

      <main className="flex min-w-0 flex-1 flex-col pb-24 lg:pb-0">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-line glass px-5 py-3 lg:px-10">
          <div className="flex items-center gap-2 lg:hidden">
            <div className="grid h-8 w-8 place-items-center rounded-lg gradient-primary text-white">
              <Sparkles size={16} />
            </div>
            <span className="text-sm font-bold text-ink">Aria</span>
          </div>
          <p className="hidden text-sm font-medium text-muted lg:block">{today}</p>
          <AccountMenu />
        </header>

        <div className="mx-auto w-full max-w-5xl flex-1 px-5 py-8 lg:px-10 lg:py-10">
          {error && (
            <div className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
              {error}
            </div>
          )}
          {view === "agent" && (
            <AgentView
              name={name} value={value} setValue={setValue} onRun={onRun}
              running={running} messages={messages} status={status}
              prompt={prompt} onResume={onResume} history={history}
            />
          )}
          {view === "history" && <HistoryView />}
          {view === "profile" && <ProfileView />}
          {view === "settings" && <SettingsView />}
        </div>
      </main>

      <BottomNav active={view} onSelect={setView} />
    </div>
  );
}
