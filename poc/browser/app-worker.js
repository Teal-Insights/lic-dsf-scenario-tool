import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

const base = new URL(".", self.location.href);
let pyodide;

function say(text) {
  self.postMessage({ type: "status", text });
}

function fail(error) {
  const raw = typeof error?.message === "string" ? error.message : "";
  const lines = raw.split("\n").map((item) => item.trim()).filter((item) => item && !item.startsWith("at "));
  const detail = [...lines].reverse().find((item) => /Error|Exception/.test(item)) || lines.at(-1) || "";
  const cleaned = detail.replace(/^[\w.]+Error:\s*/, "").replace(/\/\S+/g, "").trim();
  const text = (cleaned || "The in-browser runtime could not start.").slice(0, 300);
  console.error(error);
  self.postMessage({ type: "fatal", message: text });
}

function syncfs(populate) {
  return new Promise((resolve, reject) => {
    pyodide.FS.syncfs(populate, (err) => (err ? reject(err) : resolve()));
  });
}

const queue = [];
let working = false;

function enqueue(task) {
  return new Promise((resolve, reject) => {
    queue.push(async () => {
      try {
        resolve(await task());
      } catch (error) {
        reject(error);
      }
    });
    drain();
  });
}

async function drain() {
  if (working) return;
  working = true;
  try {
    while (queue.length) {
      const task = queue.shift();
      await task();
    }
  } finally {
    working = false;
    if (queue.length) drain();
  }
}

async function boot() {
  say("Loading the Python runtime. The first start downloads it and can take several minutes.");
  const manifest = await (await fetch(new URL("manifest.json", base))).json();
  pyodide = await loadPyodide({ indexURL: manifest.pyodide });
  say("Loading the calculation library and chart renderer.");
  await pyodide.loadPackage([...manifest.pyodide_packages, "matplotlib"]);
  const wheels = manifest.wheels.map((name) => new URL(name, base).href);
  pyodide.globals.set("wheel_urls", pyodide.toPy(wheels));
  await pyodide.runPythonAsync(`
import os
os.environ["MPLBACKEND"] = "Agg"
import micropip
for url in wheel_urls:
    await micropip.install(url, deps=False)
`);
  if (!pyodide.FS.analyzePath("/workspace").exists) pyodide.FS.mkdir("/workspace");
  pyodide.FS.mount(pyodide.FS.filesystems.IDBFS, {}, "/workspace");
  say("Opening saved work in this browser.");
  await syncfs(true);
  pyodide.runPython(await (await fetch(new URL("runtime.py", base))).text());
  pyodide.runPython("prepare()");
  pyodide.runPython(await (await fetch(new URL("session.py", base))).text());
  pyodide.runPython("open_session('/workspace')");
  await syncfs(false);
  self.postMessage({ type: "ready" });
  say("Loading the workspace.");
}

async function handle(message) {
  if (message.type === "sync") {
    await syncfs(false);
    return;
  }
  if (message.type === "calculate-job") {
    say("Calculating your saved scenario. The first run loads the model and can take several minutes.");
    pyodide.globals.set("calc_job_id", message.jobId);
    pyodide.runPython("run_calculation(calc_job_id)");
    await syncfs(false);
    say("Calculation finished.");
    return;
  }
  if (message.type !== "request") return;
  try {
    const target = String(message.target || "");
    if (target.split("?")[0] === "/api/example" && !pyodide.runPython("SESSION.official_example_cached()")) {
      say("Fetching the official illustrative template.");
      try {
        const response = await fetch(new URL("official-example.xlsm", base));
        if (response.ok) {
          pyodide.FS.writeFile("/tmp/official-example.xlsm", new Uint8Array(await response.arrayBuffer()));
        }
      } catch (error) {
        console.error(error);
      }
    }
    const bytes = message.body ? new Uint8Array(message.body) : new Uint8Array();
    pyodide.FS.writeFile("/tmp/request-body", bytes);
    pyodide.globals.set("req_method", message.method || "GET");
    pyodide.globals.set("req_target", target);
    pyodide.globals.set("req_headers", JSON.stringify(message.headers || {}));
    const meta = JSON.parse(pyodide.runPython("dispatch_request()"));
    const file = pyodide.FS.readFile("/tmp/response-body");
    const copy = new Uint8Array(file);
    self.postMessage({
      type: "response",
      id: message.id,
      status: meta.status,
      contentType: meta.content_type,
      persist: meta.persist,
      calculate: meta.calculate,
      body: copy.buffer,
    }, [copy.buffer]);
  } catch (error) {
    console.error(error);
    const payload = new TextEncoder().encode('{"error":"The in-browser workspace could not answer. Saved work is retained."}');
    self.postMessage({
      type: "response",
      id: message.id,
      status: 400,
      contentType: "application/json",
      persist: false,
      calculate: null,
      body: payload.buffer,
    }, [payload.buffer]);
  }
}

self.addEventListener("message", (event) => {
  enqueue(() => handle(event.data)).catch((error) => console.error(error));
});

boot().catch(fail);
