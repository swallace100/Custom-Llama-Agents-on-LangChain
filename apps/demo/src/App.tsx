import React, { useEffect, useState } from "react";

interface HealthResponse {
  ok: boolean;
  env: string;
  llama_url: string;
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://localhost:8080/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: 24 }}>
      <h1>Custom Llama Agents — Demo</h1>
      <p>Vite + React + TypeScript container is running.</p>

      <h2>API Health</h2>
      {error && <pre style={{ color: "crimson" }}>{error}</pre>}
      <pre>{JSON.stringify(health, null, 2)}</pre>
    </main>
  );
}
