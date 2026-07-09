import { useEffect, useRef, useState } from "react";
import { WS_BASE } from "../api";

// Opens /ws/{taskId}, accumulating messages. Surfaces the latest human-in-the-loop
// prompt (form preview / email confirm / proactive) when status is needs_input.
export function useTaskSocket(taskId) {
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState(null);
  const [prompt, setPrompt] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!taskId) return;
    setMessages([]); setStatus("connecting"); setPrompt(null);

    const ws = new WebSocket(`${WS_BASE}/ws/${taskId}`);
    wsRef.current = ws;
    ws.onopen = () => setStatus("running");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, data]);
      if (data.status) setStatus(data.status);
      if (data.status === "needs_input" && data.prompt) setPrompt(data.prompt);
      else if (data.status === "running") setPrompt(null);
    };
    ws.onerror = () => setStatus("failed");
    return () => ws.close();
  }, [taskId]);

  return { messages, status, prompt, clearPrompt: () => setPrompt(null) };
}
