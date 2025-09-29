export async function agentsGenerate(task: string, prompt: string, maxNewTokens = 256) {
  const r = await fetch(`${API_URL}/agents/generate`, {
    method: "POST",
    headers: {"content-type":"application/json"},
    body: JSON.stringify({ task, prompt, max_new_tokens: maxNewTokens })
  });
  if (!r.ok) throw new Error("agents/generate failed");
  return r.json() as Promise<{ adapter: string; text: string }>;
}
