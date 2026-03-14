#!/usr/bin/env node
import process from "node:process";
import { Codex } from "@openai/codex-sdk";

function writeLine(payload) {
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

async function readStdinJson() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.from(chunk));
  }
  const raw = Buffer.concat(chunks).toString("utf8").trim();
  if (!raw) {
    return {};
  }
  return JSON.parse(raw);
}

async function main() {
  try {
    const payload = await readStdinJson();
    const input = typeof payload.input === "string" ? payload.input : "";
    if (!input.trim()) {
      throw new Error("input is required");
    }

    const options = {};
    if (typeof payload.model === "string" && payload.model.trim()) {
      options.model = payload.model.trim();
    }
    if (typeof payload.workingDirectory === "string" && payload.workingDirectory.trim()) {
      options.workingDirectory = payload.workingDirectory.trim();
    }
    if (typeof payload.skipGitRepoCheck === "boolean") {
      options.skipGitRepoCheck = payload.skipGitRepoCheck;
    }
    if (typeof payload.networkAccessEnabled === "boolean") {
      options.networkAccessEnabled = payload.networkAccessEnabled;
    }

    const codexOptions = {};
    if (payload.codexEnv && typeof payload.codexEnv === "object") {
      codexOptions.env = payload.codexEnv;
    }
    if (payload.configOverrides && typeof payload.configOverrides === "object") {
      codexOptions.config = payload.configOverrides;
    }

    const codex = new Codex(codexOptions);
    const thread = codex.startThread(options);
    const { events } = await thread.runStreamed(input);

    let text = "";
    const byMessageId = new Map();
    let usage = {};

    for await (const event of events) {
      const evtType = typeof event?.type === "string" ? event.type : "";
      if (evtType === "response.output_text.delta" || evtType === "output_text.delta") {
        const delta = typeof event.delta === "string" ? event.delta : "";
        if (delta) {
          text += delta;
        }
        continue;
      }

      if (evtType === "item.started" || evtType === "item.updated" || evtType === "item.completed") {
        const item = event.item;
        if (item && item.type === "agent_message" && typeof item.text === "string" && item.text) {
          const msgId = String(item.id || "agent-message");
          const previous = byMessageId.get(msgId) || "";
          const delta = item.text.startsWith(previous) ? item.text.slice(previous.length) : item.text;
          if (delta) {
            text += delta;
          }
          byMessageId.set(msgId, item.text);
        }
        continue;
      }

      if (evtType === "turn.completed" && event.usage && typeof event.usage === "object") {
        usage = event.usage;
        continue;
      }

      if (evtType === "turn.failed" || evtType === "error") {
        const message = event.error?.message || event.message || "codex turn failed";
        throw new Error(String(message));
      }
    }

    writeLine({ ok: true, text, usage });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    writeLine({ ok: false, error: message });
    process.exitCode = 1;
  }
}

await main();
