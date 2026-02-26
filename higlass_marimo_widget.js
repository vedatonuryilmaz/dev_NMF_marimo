import * as hglib from "https://esm.sh/higlass@1.13?deps=react@17,react-dom@17,pixi.js@6";

const JUPYTER_SERVER_NAME = "jupyter";

/**
 * @typedef State
 * @property {Object} _viewconf
 * @property {Record<string, unknown>} _options
 * @property {Array<string>} _plugin_urls
 * @property {Array<number> | Array<Array<number>>} location
 * @property {string} status
 * @property {number} height
 */

function setStatus(model, status) {
  model.set("status", status);
  model.save_changes();
}

/**
 * @param {string} href
 * @returns {Promise<void>}
 */
function loadScript(href) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${href}"]`) !== null) {
      resolve();
      return;
    }

    const script = document.createElement("script");
    script.src = href;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load ${href}`));
    document.head.appendChild(script);
  });
}

/**
 * @param {Array<string>} pluginUrls
 * @returns {Promise<void>}
 */
async function requireScripts(pluginUrls) {
  const backup = {
    // @ts-expect-error - not always available on Window typing
    define: window.define,
    require: window.require,
    // @ts-expect-error - not always available on Window typing
    requirejs: window.requirejs,
  };

  for (const field of Object.keys(backup)) {
    // @ts-expect-error - dynamic field mutation on Window
    window[field] = undefined;
  }

  const results = await Promise.allSettled((pluginUrls ?? []).map(loadScript));
  results.forEach((result, i) => {
    if (result.status === "rejected") {
      console.warn(`Failed to load script: ${pluginUrls[i]}`, result.reason);
    }
  });

  Object.assign(window, backup);
}

/**
 * @param {any} view
 * @returns {Array<any>}
 */
function collectTracks(view) {
  const tracks = Object.values(view?.tracks ?? {}).flat();
  const expanded = [...tracks];

  for (const track of tracks) {
    if (Array.isArray(track?.contents)) {
      expanded.push(...track.contents);
    }
  }

  return expanded;
}

/**
 * @param {any} viewconf
 * @returns {boolean}
 */
function hasJupyterServerTracks(viewconf) {
  for (const view of viewconf?.views ?? []) {
    const tracks = collectTracks(view);
    for (const track of tracks) {
      if (track?.server === JUPYTER_SERVER_NAME) {
        return true;
      }
    }
  }
  return false;
}

/**
 * @param {any} viewconf
 * @returns {any}
 */
function resolveJupyterServers(viewconf) {
  const copy = JSON.parse(JSON.stringify(viewconf));

  for (const view of copy?.views ?? []) {
    const tracks = collectTracks(view);
    for (const track of tracks) {
      if (track?.server === JUPYTER_SERVER_NAME) {
        delete track.server;
        track.data = track.data ?? {};
        track.data.type = JUPYTER_SERVER_NAME;
        track.data.tilesetUid = track.tilesetUid;
      }
    }
  }

  return copy;
}

/**
 * @param {{ xDomain: [number, number], yDomain: [number, number] }} location
 * @returns {[number, number, number, number]}
 */
function locationToCoordinates(location) {
  const [x, xe] = location.xDomain;
  const [y, ye] = location.yDomain;
  return [x, xe, y, ye];
}

/**
 * @param {HTMLElement} el
 * @param {number} height
 */
function syncHostDimensions(el, height) {
  const safeHeight = Number.isFinite(height) ? Math.max(320, Math.floor(height)) : 1120;
  el.style.width = "100%";
  el.style.height = `${safeHeight}px`;
  el.style.minHeight = `${safeHeight}px`;
}

/**
 * @param {HTMLElement} el
 * @returns {HTMLElement}
 */
function ensureContainer(el) {
  let container = el.querySelector(".hg-marimo-root");
  if (!container) {
    container = document.createElement("div");
    container.className = "hg-marimo-root";
    el.appendChild(container);
  }
  container.style.width = "100%";
  container.style.height = "100%";
  return container;
}

/**
 * @param {HTMLElement} el
 * @returns {() => void}
 */
function addEventListenersTo(el) {
  const controller = new AbortController();
  el.addEventListener("contextmenu", (event) => event.stopPropagation(), {
    signal: controller.signal,
  });
  return () => controller.abort();
}

/**
 * @param {import("npm:@anywidget/types").AnyModel<State>} model
 * @param {HTMLElement} el
 * @returns {Promise<() => void>}
 */
async function mountViewer(model, el) {
  setStatus(model, "loading");
  syncHostDimensions(el, model.get("height"));
  const container = ensureContainer(el);
  container.replaceChildren();

  const pluginUrls = model.get("_plugin_urls") ?? [];
  await requireScripts(pluginUrls);

  const originalViewconf = model.get("_viewconf");
  const usesJupyterServer = hasJupyterServerTracks(originalViewconf);
  if (usesJupyterServer) {
    setStatus(model, "unsupported-jupyter-server-track");
  }

  const viewconf = resolveJupyterServers(originalViewconf);
  const options = model.get("_options") ?? {};
  const api = await hglib.viewer(container, viewconf, options);
  setStatus(model, "viewer-ready");

  const unlisten = addEventListenersTo(container);

  const onCustomMessage = (rawMsg) => {
    try {
      const msg = JSON.parse(rawMsg);
      const [fn, ...args] = msg;
      if (typeof api[fn] === "function") {
        api[fn](...args);
      }
    } catch (error) {
      console.warn("HiGlass custom message handling failed", error);
    }
  };
  model.on("msg:custom", onCustomMessage);

  if ((viewconf?.views ?? []).length === 1) {
    api.on(
      "location",
      (loc) => {
        model.set("location", locationToCoordinates(loc));
        model.save_changes();
      },
      viewconf.views[0].uid,
    );
  } else {
    (viewconf?.views ?? []).forEach((view, idx) => {
      api.on("location", (loc) => {
        const previous = model.get("location");
        const location = Array.isArray(previous) ? previous.slice() : [];
        location[idx] = locationToCoordinates(loc);
        model.set("location", location);
        model.save_changes();
      }, view.uid);
    });
  }

  const firstView = viewconf?.views?.[0];
  if (firstView?.uid && Array.isArray(firstView.initialXDomain)) {
    const [xStart, xEnd] = firstView.initialXDomain;
    setTimeout(() => {
      try {
        api.zoomTo(firstView.uid, xStart, xEnd, null, null, 0);
      } catch (error) {
        console.warn("Initial zoomTo refresh failed", error);
      }
    }, 0);
  }

  const observer = new ResizeObserver(() => {
    if (typeof api.refreshView === "function") {
      api.refreshView();
    }
  });
  observer.observe(container);

  return () => {
    observer.disconnect();
    model.off("msg:custom", onCustomMessage);
    unlisten();
    if (typeof api.destroy === "function") {
      api.destroy();
    }
  };
}

export default {
  /** @type {import("npm:@anywidget/types").Render<State>} */
  async render({ model, el }) {
    let disposed = false;
    let cleanup = () => {};
    let mountVersion = 0;

    async function remount() {
      const version = ++mountVersion;
      cleanup();
      cleanup = () => {};
      try {
        cleanup = await mountViewer(model, el);
      } catch (error) {
        console.error("HiGlass mount failed", error);
        if (!disposed && version === mountVersion) {
          setStatus(model, `failed: ${error?.message ?? "unknown"}`);
        }
      }
    }

    await remount();

    const onViewconf = () => {
      if (!disposed) {
        void remount();
      }
    };
    const onOptions = () => {
      if (!disposed) {
        void remount();
      }
    };
    const onPluginUrls = () => {
      if (!disposed) {
        void remount();
      }
    };
    const onHeight = () => {
      syncHostDimensions(el, model.get("height"));
    };

    model.on("change:_viewconf", onViewconf);
    model.on("change:_options", onOptions);
    model.on("change:_plugin_urls", onPluginUrls);
    model.on("change:height", onHeight);

    return () => {
      disposed = true;
      model.off("change:_viewconf", onViewconf);
      model.off("change:_options", onOptions);
      model.off("change:_plugin_urls", onPluginUrls);
      model.off("change:height", onHeight);
      cleanup();
    };
  },
};
