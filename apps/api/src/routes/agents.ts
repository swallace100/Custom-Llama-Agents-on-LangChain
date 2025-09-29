// apps/api/src/routes/agents.ts
import express from "express";
import fetch from "node-fetch";
const router = express.Router();

router.post("/agents/generate", async (req, res) => {
  const r = await fetch("http://llm_host_py:7001/generate", {
    method: "POST",
    headers: {"content-type":"application/json"},
    body: JSON.stringify(req.body),
  });
  const data = await r.json();
  res.json(data);
});
export default router;
