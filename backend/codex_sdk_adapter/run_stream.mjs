#!/usr/bin/env node
import process from "node:process";
import { Codex } from "@openai/codex-sdk";

function writeEvent(event) {
  process.stdout.write(`${JSON.stringify(event)}\n`);
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
    if (!input) {
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

    const codex = new Codex();
    const thread = codex.startThread(options);
    const { events } = await thread.runStreamed(input);

    for await (const event of events) {
      writeEvent(event);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    writeEvent({
      type: "turn.failed",
      error: { message },
    });
    process.exitCode = 1;
  }
}

await main();
