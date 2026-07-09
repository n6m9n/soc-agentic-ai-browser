import { useState } from "react";

// The command input bar. Calls onSubmit(command) on Enter / button click.
export default function CommandBar({ onSubmit, disabled }) {
  const [value, setValue] = useState("");

  function submit(e) {
    e.preventDefault();
    const command = value.trim();
    if (!command) return;
    onSubmit(command);
    setValue("");
  }

  return (
    <form onSubmit={submit} className="flex gap-2">
      <input
        className="flex-1 rounded-lg border border-slate-300 px-4 py-3 text-sm
                   focus:outline-none focus:ring-2 focus:ring-indigo-500"
        placeholder='Try: "go to google.com and search for AI news"'
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
      />
      <button
        type="submit"
        disabled={disabled}
        className="rounded-lg bg-indigo-600 px-5 py-3 text-sm font-medium text-white
                   hover:bg-indigo-700 disabled:opacity-50"
      >
        {disabled ? "Running…" : "Run"}
      </button>
    </form>
  );
}
