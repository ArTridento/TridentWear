const ERROR_BUFFER_KEY = "tridentwear-frontend-errors";

function readBuffer() {
  try {
    return JSON.parse(localStorage.getItem(ERROR_BUFFER_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeBuffer(entries) {
  try {
    localStorage.setItem(ERROR_BUFFER_KEY, JSON.stringify(entries.slice(-25)));
  } catch {
    /* Monitoring should never break the storefront. */
  }
}

export function logFrontendError(error, context = {}) {
  const entry = {
    message: error?.message || String(error),
    stack: error?.stack || "",
    path: window.location.pathname,
    request_id: context.request_id || error?.request_id || null,
    context,
    created_at: new Date().toISOString(),
  };
  writeBuffer([...readBuffer(), entry]);
  if (window.__TRIDENT_ENABLE_CONSOLE_MONITORING !== false) {
    console.error("[TridentWear]", entry);
  }
}

export function initErrorMonitoring() {
  window.addEventListener("error", (event) => {
    logFrontendError(event.error || event.message, { source: "window.error" });
  });
  window.addEventListener("unhandledrejection", (event) => {
    logFrontendError(event.reason || "Unhandled promise rejection", { source: "unhandledrejection" });
  });
}
