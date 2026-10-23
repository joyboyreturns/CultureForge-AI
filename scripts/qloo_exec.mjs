#!/usr/bin/env node
/**
 * qloo_exec.mjs - run a Qloo workflow with a request timeout the qloo CLI cannot set.
 *
 * WHY THIS EXISTS
 * The qloo CLI's `exec` path builds its HTTP client without a `timeoutMs`, so it
 * always uses the harness default of 20s per attempt. The /v2/insights endpoint
 * that `recommend` calls routinely takes ~25s against the hackathon environment,
 * so every request exceeds the cap, is retried up to 3 times, and still fails.
 * That burns 3 API calls to produce no result.
 *
 * This wrapper reuses the harness's own client and workflow executor, but sets
 * the per-request timeout explicitly (QLOO_REQUEST_TIMEOUT_MS, default 60000).
 * It is a drop-in replacement for the `qloo` binary:
 *
 *   qloo      exec find_tags --input-file req.json
 *   qloo_exec.mjs exec find_tags --input-file req.json
 *
 * Same arguments, same stdout contract, same exit codes.
 *
 * Env:
 *   QLOO_REQUEST_TIMEOUT_MS  per-attempt HTTP timeout in ms (default 60000)
 *   QLOO_MAX_ATTEMPTS        HTTP attempts per request (default 1 - no blind retries)
 *   QLOO_HARNESS_PATH        explicit path to the @qloo/qloo-harness package
 */

import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const TIMEOUT_MS = Number(process.env.QLOO_REQUEST_TIMEOUT_MS ?? 60000);
// One attempt by default: the provider does its own bounded retry, and the
// harness default of 3 attempts multiplies quota consumption by 3.
const MAX_ATTEMPTS = Number(process.env.QLOO_MAX_ATTEMPTS ?? 1);

function fail(message) {
  process.stderr.write(`qloo_exec: ${message}\n`);
  process.exit(1);
}

/** Locate the globally installed @qloo/qloo-harness package. */
function resolveHarnessDir() {
  const explicit = process.env.QLOO_HARNESS_PATH?.trim();
  if (explicit && existsSync(join(explicit, "dist", "exec.js"))) return explicit;

  const candidates = [];
  const npmRoot = spawnSync("npm", ["root", "-g"], { encoding: "utf8" });
  if (npmRoot.status === 0 && npmRoot.stdout.trim()) candidates.push(npmRoot.stdout.trim());
  candidates.push(
    join(homedir(), ".local", "lib", "node_modules"),
    join(homedir(), ".npm-global", "lib", "node_modules"),
    "/usr/local/lib/node_modules",
    "/opt/homebrew/lib/node_modules"
  );

  for (const root of candidates) {
    const dir = join(root, "@qloo", "qloo-harness");
    if (existsSync(join(dir, "dist", "exec.js"))) return dir;
  }
  return null;
}

/** Find the chunk module that exports QlooClient (the file name varies by version). */
async function resolveClientChunk(distDir) {
  const chunksDir = join(distDir, "chunks");
  if (!existsSync(chunksDir)) return null;
  const preferred = join(chunksDir, "chunk-ESNY4EJL.js");
  if (existsSync(preferred)) {
    try {
      const mod = await import(pathToFileURL(preferred).href);
      if (mod.QlooClient) return preferred;
    } catch {
      /* fall through to the scan */
    }
  }
  for (const name of readdirSync(chunksDir)) {
    if (!name.endsWith(".js")) continue;
    const file = join(chunksDir, name);
    try {
      const mod = await import(pathToFileURL(file).href);
      if (mod.QlooClient) return file;
    } catch {
      /* not the module we want */
    }
  }
  return null;
}

const harnessDir = resolveHarnessDir();
if (!harnessDir) {
  fail(
    "could not locate @qloo/qloo-harness. Install it with:\n" +
      "  npm install --global @qloo/qloo-harness\n" +
      "or set QLOO_HARNESS_PATH to the package directory."
  );
}

const distDir = join(harnessDir, "dist");
const clientChunk = await resolveClientChunk(distDir);
if (!clientChunk) fail("could not locate the QlooClient module inside the harness.");

const { QlooClient, resolveQlooClientConfiguration } = await import(pathToFileURL(clientChunk).href);
const { createDirectQlooWorkflowExecutor } = await import(pathToFileURL(join(distDir, "qloo-tools.js")).href);
const { createQlooResolutionProviderFromEnvironment } = await import(
  pathToFileURL(join(distDir, "resolution-provider.js")).href
);
const { runQlooExec } = await import(pathToFileURL(join(distDir, "exec.js")).href);

const resolved = resolveQlooClientConfiguration({ env: process.env });
if (!resolved.apiKey) {
  fail("no Qloo API key. Run `qloo config set api-key YOUR_KEY` or set QLOO_API_KEY.");
}

const client = new QlooClient({
  apiKey: resolved.apiKey,
  ...resolved.baseUrl ? { baseUrl: resolved.baseUrl } : {},
  allowCustomBaseUrl: resolved.baseUrlTrusted,
  timeoutMs: TIMEOUT_MS,
  maxAttempts: MAX_ATTEMPTS
});

const resolutionProvider = createQlooResolutionProviderFromEnvironment({
  client,
  env: process.env,
  fileConfig: resolved.fileConfig
});

const executor = createDirectQlooWorkflowExecutor(client, undefined, resolutionProvider);

// Drop a leading "exec" so this script can stand in for the qloo binary.
const argv = process.argv.slice(2);
if (argv[0] === "exec") argv.shift();

// A deliberately narrow raw Insights path for the typed evidence challenge.
// The public harness `recommend` schema currently rejects entity exclusions,
// although Qloo's Insights endpoint supports `filter.exclude.entities`.
// Backend code constructs and validates the payload; this wrapper enforces
// the same fixed key set before sending it and makes exactly one attempt.
if (argv[0] === "insights_probe") {
  const inputIndex = argv.indexOf("--input-file");
  if (inputIndex < 0 || !argv[inputIndex + 1]) {
    process.stdout.write(JSON.stringify({ error: { code: "TOOL_INPUT" } }));
    process.exitCode = 2;
  } else {
    try {
      const query = JSON.parse(readFileSync(argv[inputIndex + 1], "utf8"));
      const allowed = new Set([
        "filter.type", "signal.interests.tags", "operator.signal.interests.tags",
        "filter.location.query", "filter.exclude.entities", "take",
        "feature.explainability",
      ]);
      if (!query || typeof query !== "object" || Array.isArray(query) ||
          Object.keys(query).some((key) => !allowed.has(key)) ||
          query["filter.type"] !== "urn:entity:place" ||
          typeof query["signal.interests.tags"] !== "string" ||
          !query["signal.interests.tags"].length ||
          typeof query["filter.location.query"] !== "string" ||
          typeof query["filter.exclude.entities"] !== "string") {
        process.stdout.write(JSON.stringify({ error: { code: "TOOL_INPUT" } }));
        process.exitCode = 2;
      } else {
        const probeClient = new QlooClient({
          apiKey: resolved.apiKey,
          ...resolved.baseUrl ? { baseUrl: resolved.baseUrl } : {},
          allowCustomBaseUrl: resolved.baseUrlTrusted,
          timeoutMs: TIMEOUT_MS,
          maxAttempts: 1,
        });
        const response = await probeClient.insights(query);
        const resultEntities = Array.isArray(response?.results?.entities)
          ? response.results.entities : [];
        process.stdout.write(JSON.stringify({
          status: "ok", results: { entities: resultEntities },
          query: response?.query ?? {},
          provenance: { requests: ["GET /v2/insights"] },
        }) + "\n");
      }
    } catch (error) {
      process.stdout.write(JSON.stringify({ error: {
        code: error?.code ?? "QLOO_REJECTED",
        status: Number.isInteger(error?.status) ? error.status : undefined,
        retryable: Boolean(error?.retryable),
        message: error?.message ?? "Qloo rejected the Insights request.",
      }}) + "\n");
      process.exitCode = 1;
    }
  }
} else {
  process.exitCode = await runQlooExec(argv, { createExecutor: () => executor });
}
