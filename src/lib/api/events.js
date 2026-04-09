const listeners = new Map();

function getEventBucket(eventName) {
  const bucket = listeners.get(eventName) || new Set();
  listeners.set(eventName, bucket);
  return bucket;
}

export async function listen(eventName, callback) {
  const handler = callback || (() => {});
  const bucket = getEventBucket(eventName);
  bucket.add(handler);

  const windowHandler = (event) => {
    handler({ payload: event.detail });
  };
  window.addEventListener(eventName, windowHandler);

  return async () => {
    bucket.delete(handler);
    if (!bucket.size) {
      listeners.delete(eventName);
    }
    window.removeEventListener(eventName, windowHandler);
  };
}

export function emitLocalEvent(eventName, payload) {
  window.dispatchEvent(new CustomEvent(eventName, { detail: payload }));
}
