import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

const base = new URL(".", self.location.href);
let pyodide;

function say(text) {
  self.postMessage({ type: "status", text });
}

function fail(error) {
  const raw = typeof error?.message === "string" ? error.message : "";
  const detail = raw.split("\n").map((item) => item.trim()).find((item) => item && !item.startsWith("See:") && !item.startsWith("at ") && !item.startsWith("Traceback")) || "";
  const cleaned = detail.replace(/^[\w.]+Error:\s*/, "").trim();
  const code = error && (error.code || (error.errno != null ? "errno " + error.errno : ""));
  const name = error?.constructor?.name;
  const text = [code, cleaned].filter(Boolean).join(": ") || (name && name !== "Error" ? name : "") || "Calculation failed.";
  self.postMessage({ type: "error", message: String(text).slice(0, 400) });
}

function writeWorkbook(buffer) {
  if (!pyodide.FS.analyzePath("/work").exists) pyodide.FS.mkdir("/work");
  pyodide.FS.writeFile("/work/upload.xlsm", new Uint8Array(buffer));
}

async function boot() {
  say("Loading the Python runtime.");
  const manifest = await (await fetch(new URL("manifest.json", base))).json();
  pyodide = await loadPyodide({ indexURL: manifest.pyodide });
  say("Loading the calculation library.");
  await pyodide.loadPackage(manifest.pyodide_packages);
  const wheels = manifest.wheels.map((name) => new URL(name, base).href);
  pyodide.globals.set("wheel_urls", pyodide.toPy(wheels));
  await pyodide.runPythonAsync(`
import micropip
for url in wheel_urls:
    await micropip.install(url, deps=False)
`);
  const source = await (await fetch(new URL("runtime.py", base))).text();
  pyodide.runPython(source);
  pyodide.runPython("prepare()");
  self.postMessage({ type: "ready" });
  say("Choose a workbook. It stays in this browser.");
}

self.onmessage = async (event) => {
  const message = event.data;
  try {
    if (message.type === "inspect" || message.type === "calculate") {
      writeWorkbook(message.buffer);
    }
    if (message.type === "inspect") {
      say("Checking the workbook.");
      const payload = JSON.parse(pyodide.runPython("inspect_upload('/work/upload.xlsm')"));
      self.postMessage({ type: "inspected", payload });
      say(payload.status === "supported" ? "Workbook checked. Choose a case and calculate." : "This workbook is not a supported template.");
      return;
    }
    if (message.type === "calculate") {
      say("Calculating. The first run loads the model and can take several minutes.");
      const started = performance.now();
      pyodide.globals.set("scenario_json", JSON.stringify(message.definition));
      const payload = JSON.parse(pyodide.runPython("calculate_upload('/work/upload.xlsm', scenario_json)"));
      self.postMessage({ type: "result", payload, seconds: (performance.now() - started) / 1000 });
      say("Calculation finished. The workbook was not stored.");
    }
  } catch (error) {
    fail(error);
  }
};

boot().catch(fail);
