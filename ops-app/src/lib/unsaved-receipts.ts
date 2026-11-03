// Receipts the service sent but could not save, kept for the rep until dismissed.
// One store for the whole page, so a receipt arriving after its booking's row moved
// between tables, or was replaced by a refresh, still shows. Browser storage keeps it
// across reloads when the browser allows it. Client components only.
const PREFIX = "unsaved-receipt:";
const EMPTY: Record<string, string> = {};

let receipts: Record<string, string> | null = null;
const listeners = new Set<() => void>();

function stored(): Record<string, string> {
  const found: Record<string, string> = {};
  try {
    for (let i = 0; i < window.localStorage.length; i++) {
      const key = window.localStorage.key(i);
      const value = key?.startsWith(PREFIX) ? window.localStorage.getItem(key) : null;
      if (key && value !== null) found[key.slice(PREFIX.length)] = value;
    }
  } catch {
    // storage refused: receipts live in memory for this page only
  }
  return found;
}

function save(loadId: string, receipt: string | null) {
  try {
    if (receipt === null) window.localStorage.removeItem(PREFIX + loadId);
    else window.localStorage.setItem(PREFIX + loadId, receipt);
  } catch {
    // the in-memory copy still shows until the rep dismisses it
  }
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getReceipts(): Record<string, string> {
  receipts ??= stored();
  return receipts;
}

export function getServerReceipts(): Record<string, string> {
  return EMPTY;
}

export function keepReceipt(loadId: string, receipt: string) {
  receipts = { ...getReceipts(), [loadId]: receipt };
  save(loadId, receipt);
  listeners.forEach((listener) => listener());
}

export function dropReceipt(loadId: string) {
  const { [loadId]: _dropped, ...rest } = getReceipts();
  receipts = rest;
  save(loadId, null);
  listeners.forEach((listener) => listener());
}
