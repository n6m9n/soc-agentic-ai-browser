import { useEffect, useRef, useState } from "react";
import { WS_BASE } from "../api";

// Opens a WebSocket to /ws/{taskId} and accumulates the live step messages.
// Returns { messages, status }. Re-connects whenever taskId changes.
export function useTaskSocket(taskId) {
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!taskId) return;
    setMessages([]);
    setStatus("connecting");

    const ws = new WebSocket(`${WS_BASE}/ws/${taskId}`);
    wsRef.current = ws;

    ws.onopen = () => setStatus("running");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, data]);
      if (data.status) setStatus(data.status);
    };
    ws.onerror = () => setStatus("failed");
    ws.onclose = () => setStatus((s) => (s === "completed" || s === "failed" ? s : "closed"));

    return () => ws.close();
  }, [taskId]);

  return { messages, status };
}
