/* Patch same-origin /api calls so the analyst page talks to the Pyodide worker.
   The static server never receives the workbook. The page's recovery timer
   aborts a fetch after 30 seconds; the runtime download and a calculation
   can take longer, so these local calls are not tied to that timer. */
(() => {
  const banner = () => document.getElementById("browserRuntime");
  const worker = new Worker("/app-worker.js", { type: "module" });
  let readyResolve;
  let readyReject;
  const ready = new Promise((resolve, reject) => {
    readyResolve = resolve;
    readyReject = reject;
  });
  const pending = new Map();
  let nextId = 1;
  let failed = false;

  function fail(message) {
    if (failed) return;
    failed = true;
    const note = banner();
    if (note) note.textContent = message;
    readyReject(new Error(message));
  }

  worker.addEventListener("message", (event) => {
    const message = event.data;
    if (message.type === "status" && banner()) banner().textContent = message.text;
    if (message.type === "ready") readyResolve();
    if (message.type === "fatal") fail(message.message);
    if (message.type === "response") {
      const waiter = pending.get(message.id);
      if (!waiter) return;
      pending.delete(message.id);
      if (message.calculate) worker.postMessage({ type: "calculate-job", jobId: message.calculate });
      else if (message.persist) worker.postMessage({ type: "sync" });
      waiter.resolve(new Response(message.body, {
        status: message.status,
        headers: { "Content-Type": message.contentType || "application/octet-stream" },
      }));
    }
  });
  worker.addEventListener("error", () => {
    fail("The in-browser runtime could not start. Reload the page.");
  });

  const originalFetch = window.fetch.bind(window);
  window.fetch = async (input, init = {}) => {
    const rawUrl = typeof input === "string" ? input : input.url;
    const url = new URL(rawUrl, window.location.href);
    if (url.origin !== window.location.origin || !url.pathname.startsWith("/api/")) {
      return originalFetch(input, init);
    }
    await ready;
    const method = String(init.method || (typeof input === "string" ? "GET" : input.method) || "GET").toUpperCase();
    const headers = {};
    new Headers(init.headers || {}).forEach((value, key) => {
      headers[key] = value;
    });
    let body = null;
    if (init.body != null) {
      if (typeof init.body === "string") body = new TextEncoder().encode(init.body).buffer;
      else if (init.body instanceof ArrayBuffer) body = init.body;
      else if (ArrayBuffer.isView(init.body)) {
        body = init.body.buffer.slice(init.body.byteOffset, init.body.byteOffset + init.body.byteLength);
      } else if (typeof init.body.arrayBuffer === "function") body = await init.body.arrayBuffer();
    }
    const id = nextId;
    nextId += 1;
    const response = new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
    });
    worker.postMessage({
      type: "request",
      id,
      method,
      target: url.pathname + url.search,
      headers,
      body,
    }, body ? [body] : []);
    const result = await response;
    if (url.pathname === "/api/boot" && result.ok) banner()?.remove();
    return result;
  };
})();
